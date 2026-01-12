# Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
# Released under the MIT license
# https://opensource.org/licenses/MIT

"""
Container manager for selecting and configuring Docker environments.

This module provides ContainerManager which:
- Selects appropriate Docker images based on code analysis
- Prepares Docker run configurations
- Maps Python versions to container images
"""

from typing import Dict, Optional, List
from pathlib import Path
import subprocess
import os
import json
import logging
from lcr.utils.path_helper import get_resource_path

from .types import ImageRule, RunConfig, AnalysisResult

class DockerUnavailableError(Exception):
    """Raised when Docker daemon is not reachable."""
    pass

class ContainerManager:
    """
    Manages Docker container selection and configuration.
    
    This class uses CodeAnalyzer results to determine the appropriate
    Docker image and configuration for running legacy code.
    """
    
    # Advanced image selection rules
    # Evaluated in order, or by scoring.
    IMAGE_RULES: List[ImageRule] = [
        # Python 2.7 rules
        {
            "id": "py27-cv2",
            "name": "Python 2.7 + OpenCV 2.x",
            "version": "2.7", 
            "libs": ["cv2", "opencv", "numpy"], 
            "image": "lcr-py27-cv-apt", 
            "prepend_python": False,
            "triggers": ["cv2.cv", "cv2.bgsegm"] # Triggers for specific runtime
        },
        {
            "id": "py27-slim",
            "name": "Python 2.7 (Slim)",
            "version": "2.7", 
            "libs": [], 
            "image": "python:2.7-slim", 
            "prepend_python": True,
            "triggers": []
        },
        
        # Python 3.x rules
        {
            "id": "py36-ds",
            "name": "Python 3.6 Data Science",
            "version": "3.6", 
            "libs": ["sklearn", "pandas", "numpy"], 
            "image": "lcr-py36-ml-classic", 
            "prepend_python": False, # LCR images have ENTRYPOINT ["python"]
            "triggers": ["sklearn", "pandas"]
        },
        {
            "id": "py310-slim",
            "name": "Python 3.10 (Latest)",
            "version": "3.x", 
            "libs": [], 
            "image": "python:3.10-slim", 
            "prepend_python": True,
            "triggers": []
        }
    ]
    
    def __init__(self):
        """Initialize the ContainerManager."""
        self.definitions_dir = get_resource_path('definitions')
        self._metadata = None  # Lazy-loaded library metadata
        self._sync_installed_packages()  # Sync from library.json to hardcoded rules
        self._load_definitions()
        # トランザクション中のIDを追跡するセット
        self._pending_transactions = set()
    
    # --- [Phase 3] Atomic Build & Rollback Logic ---

    def get_definition(self, def_id):
        """Retrieve a definition by ID from memory."""
        return next((r for r in self.IMAGE_RULES if r.get('id') == def_id), None)

    def save_definition_provisional(self, config):
        """
        [Transaction Start]
        定義を「仮保存」状態でディスクに書き込む。
        この時点ではメモリ上のリスト(IMAGE_RULES)には正式登録しない、
        あるいは 'pending' フラグ付きで管理することを想定。
        """
        def_id = config.get("id")
        if not def_id:
            raise ValueError("Definition ID is required for atomic save.")

        # 1. 既存チェック (上書き防止)
        if self.get_definition(def_id):
            raise FileExistsError(f"Definition '{def_id}' already exists.")

        # 2. ファイル書き込み
        filepath = os.path.join(self.definitions_dir, f"{def_id}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # 3. トランザクション追跡開始
            self._pending_transactions.add(def_id)
            
            # 4. メモリ上のルールリストにも一時的に追加 (ビルドプロセスが参照できるようにするため)
            # ※ installed_packages の補完などは load_definitions と同様に行う必要あり
            # ここでは簡易的に追加
            self.IMAGE_RULES.append(config)
            
            logging.info(f"[Transaction] Started for '{def_id}'. File created at {filepath}")
            return filepath
            
        except Exception as e:
            # 書き込み失敗なら即座にクリーンアップ
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e

    def commit_definition(self, def_id):
        """
        [Transaction Commit]
        ビルド成功時に呼び出す。定義を正式なものとして確定させる。
        """
        if def_id in self._pending_transactions:
            self._pending_transactions.remove(def_id)
            logging.info(f"[Transaction] Committed '{def_id}'. Environment is ready.")
            # 必要であればここで library.json の更新や再ロードを行う
            return True
        else:
            logging.warning(f"[Transaction] Attempted to commit unknown transaction '{def_id}'")
            return False

    def rollback_definition(self, def_id):
        """
        [Transaction Rollback]
        ビルド失敗時に呼び出す。作成したJSONファイルを削除し、メモリからも消去する。
        """
        logging.warning(f"[Transaction] Rolling back '{def_id}'...")
        
        # 1. ファイル削除
        filepath = os.path.join(self.definitions_dir, f"{def_id}.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logging.info(f"[Transaction] Deleted file {filepath}")
            except OSError as e:
                logging.error(f"[Transaction] Failed to delete file {filepath}: {e}")

        # 2. メモリから削除
        self.IMAGE_RULES = [r for r in self.IMAGE_RULES if r['id'] != def_id]
        
        # 3. トランザクション管理から除外
        if def_id in self._pending_transactions:
            self._pending_transactions.remove(def_id)

    def is_transaction_pending(self, def_id):
        return def_id in self._pending_transactions

    def _load_definitions(self):
        """
        Load external JSON definitions from the definitions/ resource directory.
        Robustness: Skips invalid files and handles missing directories gracefully.
        """
        import json
        from lcr.utils.path_helper import get_resource_path
        
        try:
            def_dir = get_resource_path('definitions')
            if not def_dir.exists():
                print(f"[ContainerManager] Warning: Definitions directory not found: {def_dir}")
                return

            loaded_count = 0
            for json_file in def_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Hydration Prep
                    full_lib_data = self._load_library_metadata()
                    meta = full_lib_data.get("_meta", {})
                    golden = meta.get("golden_images", {})
                    
                    # Validation: Check required keys
                    if 'tag' not in data or 'base_image' not in data:
                        print(f"[ContainerManager] Skipping invalid definition {json_file.name}: Missing 'tag' or 'base_image'")
                        continue
                        
                    # Avoid duplicates
                    if any(r['image'] == data['tag'] for r in self.IMAGE_RULES):
                        continue
                        
                    # Create Rule
                    # definitions currently lack runtime metadata (libs, triggers), so we leave them empty.
                    # This means they won't be auto-selected easily, which is desired for Manual-only visibility initially.
                    new_rule: ImageRule = {
                        "id": json_file.stem,
                        "name": f"{json_file.stem} ({data.get('tag')})",
                        "version": "unknown", # Metadata missing in current definitions
                        "libs": [],
                        "image": data['tag'],
                        "prepend_python": False, # LCR images
                        "triggers": [],
                        "base_image": data.get('base_image'),
                        # Store extra info for UI tooltips if needed
                        "description": f"Base: {data.get('base_image')}",
                        # Layer 2 installed packages (for strict diff calculation)
                        "installed_packages": data.get('installed_packages', [])
                    }
                    
                    if not new_rule.get('installed_packages'):
                        base_img = data.get('base_image', '')
                        # 既知のゴールデンイメージ 'lcr-py36-ml-classic' を使っている場合
                        if 'lcr-py36-ml-classic' in base_img:
                            # 本家の 'py36-ds' ルールからデータをコピーする
                            source = next((r for r in self.IMAGE_RULES if r['id'] == 'py36-ds'), None)
                            if source:
                                new_rule['installed_packages'] = list(source.get('installed_packages', []))
                                print(f"[Debug] Hydrated rule '{new_rule['id']}' with installed_packages from py36-ds")
                            else:
                                print(f"[Debug] Failed to hydrate '{new_rule['id']}': Source 'py36-ds' not found.")
                        
                        # Fallback: Try Golden Image lookup by Base Image
                        if not new_rule.get('installed_packages'):
                             full_lib_data = self._load_library_metadata()
                             meta = full_lib_data.get("_meta", {})
                             golden = meta.get("golden_images", {})
                             if base_img in golden:
                                 new_rule['installed_packages'] = golden[base_img].get('pre_installed', [])
                                 print(f"[Debug] Hydrated rule '{new_rule['id']}' with installed_packages from golden['{base_img}']")
                             else:
                                 pass # print(f"[Debug] No golden record for base '{base_img}'")
                    # ---------------------------------------------------

                    self.IMAGE_RULES.append(new_rule)
                    loaded_count += 1
                    
                    # Debug: Confirm installed_packages were loaded
                    pkg_count = len(new_rule['installed_packages'])
                    print(f"[Debug] Loaded rule '{new_rule['id']}' with {pkg_count} installed package(s): {new_rule['installed_packages']}")
                    
                except Exception as e:
                    print(f"[ContainerManager] Error loading {json_file.name}: {e}")
            
            if loaded_count > 0:
                print(f"[ContainerManager] Loaded {loaded_count} external definitions.")
                
        except Exception as e:
            print(f"[ContainerManager] Critical Error loading definitions: {e}")

    def reload_definitions(self):
        """
        Reload all definitions from disk and update internal rules list.
        Preserves the hardcoded rules (first set of rules) but refreshes loaded ones.
        """
        # Keep hardcoded rules (assuming they are first 4 in current implementation)
        # Better strategy: Filter list to only keep those WITHOUT 'id' matching file pattern or use explicit mark
        # For this phase, we'll reset to initial Hardcoded Set manually or via Filter
        
        # Hardcoded IDs: py27-cv2, py27-slim, py36-ds, py310-slim
        hardcoded_ids = {"py27-cv2", "py27-slim", "py36-ds", "py310-slim"}
        self.IMAGE_RULES = [r for r in self.IMAGE_RULES if r['id'] in hardcoded_ids]
        
        # Reload from disk
        self._load_definitions()
        print("[ContainerManager] Definitions reloaded.")
    
    def _sync_installed_packages(self):
        """Sync installed_packages from library.json to hardcoded IMAGE_RULES.
        
        This ensures hardcoded rules have accurate pre-installed package lists
        without manual duplication.
        """
        meta = self._load_library_metadata().get("_meta", {})
        golden = meta.get("golden_images", {})
        
        for rule in self.IMAGE_RULES:
            image_tag = rule.get('image')
            if image_tag in golden:
                # Sync pre_installed list to rule
                rule['installed_packages'] = golden[image_tag].get('pre_installed', [])
                print(f"[ContainerManager] Synced installed_packages for '{rule['id']}': {rule['installed_packages']}")
            else:
                # No golden image data, set empty list
                rule['installed_packages'] = []
    
    def _deep_merge(self, base: Dict, overlay: Dict) -> Dict:
        """
        Recursive merge of overlay dictionary into base dictionary.
        Modifies base in-place to ensure all references are updated.
        """
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def get_library_info(self):
        """Return the loaded library metadata (including overlays)."""
        return self._load_library_metadata()

    def _load_library_metadata(self):
        """Load library.json metadata and apply enterprise.json overlay if present."""
        if self._metadata is not None:
            return self._metadata
            
        import json
        from pathlib import Path
        
        # 1. Standard Load
        try:
            mapping_path = Path(__file__).parent.parent / "detector" / "mappings" / "library.json"
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ContainerManager] Warning: Failed to load library metadata: {e}")
            data = {}

        # 2. Enterprise Overlay
        overlay_candidates = [
            mapping_path.parent / "enterprise.json", # Same dir as library.json
            Path.cwd() / "enterprise.json"           # Project root (CWD)
        ]
        
        for overlay_path in overlay_candidates:
            if overlay_path.exists():
                try:
                    with open(overlay_path, 'r', encoding='utf-8') as f:
                        overlay_data = json.load(f)
                    
                    self._deep_merge(data, overlay_data)
                    print(f"[Enterprise] Enterprise overlay mapping applied from {overlay_path.name}")
                    
                except json.JSONDecodeError:
                    print(f"[Enterprise] Warning: Invalid JSON in {overlay_path}. Skipping.")
                except Exception as e:
                    print(f"[Enterprise] Warning: Failed to load {overlay_path}: {e}")

        # Store FULL data, not just _meta, to support custom library definitions
        self._metadata = data
        return self._metadata
    
    def _extract_version(self, base_rule):
        """Extract major.minor version from rule (e.g., '3.6', '2.7').
        
        Returns:
            String like '3.6', '2.7', or None if cannot determine
        """
        import re
        
        # Try rule['version'] first
        version_str = base_rule.get('version', '')
        if version_str:
            # Extract x.y pattern
            match = re.search(r'(\d+\.\d+)', version_str)
            if match:
                return match.group(1)
        
        # Fallback: Try parsing from image tag
        image = base_rule.get('image', '')
        match = re.search(r'(\d+\.\d+)', image)
        if match:
            return match.group(1)
            
        return None
    
    def _apply_legacy_pins(self, pip_packages, python_version):
        """
        Pythonバージョンに基づき、特定のパッケージを安定版に固定する。
        名前の正規化（ハイフン/アンダースコア/小文字）を行い、表記揺れを吸収する。
        """
        if not pip_packages:
            return []

        # 1. library.json から該当バージョンのピン留めテーブルを取得
        meta = self._load_library_metadata().get("_meta", {})
        legacy_map = meta.get('legacy_versions', {})
        
        # バージョンキー (例: "3.6") の部分一致検索
        target_pins = {}
        for ver_key, pins in legacy_map.items():
            if ver_key in python_version:
                target_pins = pins
                break
        
        if not target_pins:
            return pip_packages

        # 2. ピン留め辞書のキーを正規化して検索用マップを作る
        # 例: "scikit-image" -> "scikit_image"
        def normalize(name):
            return name.lower().replace('-', '_').replace('.', '')

        normalized_pins = {normalize(k): v for k, v in target_pins.items()}

        # 3. パッケージリストを走査して置換
        result = []
        for pkg in pip_packages:
            # バージョン指定を取り除いて名前だけにする
            pkg_name = pkg.split('==')[0].split('>=')[0].split('<')[0].strip()
            norm_name = normalize(pkg_name)

            if norm_name in normalized_pins:
                # マッチした！ -> 強制的にバージョンを付与した文字列にする
                pin_version = normalized_pins[norm_name]
                
                # library.json の値が "==0.17.2" のように演算子込みか確認が必要
                pinned_pkg = f"{pkg_name}{pin_version}"
                
                print(f"[Legacy Pin] Applied {pin_version} to '{pkg_name}'")
                result.append(pinned_pkg)
            else:
                result.append(pkg)

        return result
    
    def _subtract_golden_packages(self, packages, base_rule):
        """Remove packages already in golden image to avoid conflicts.
        
        Args:
            packages: List of package names to install
            base_rule: Base image rule dictionary
            
        Returns:
            Tuple of (filtered_packages, removed_packages) where:
            - filtered_packages: List with pre-installed packages removed
            - removed_packages: List of package names that were skipped
        """
        # Super-normalization: Unify all package name variations
        def normalize_pkg_name(name):
            """Super-normalize package name: lowercase + replace hyphens with underscores + remove dots."""
            return name.lower().replace('-', '_').replace('.', '')
        
        # Priority 1: Check if base_rule has installed_packages from definition file
        pre_installed = set()
        
        # Try to get from loaded definition file (stored in rule metadata)
        if 'installed_packages' in base_rule:
            pre_installed = set(base_rule.get('installed_packages', []))
            print(f"[Golden Image] Using installed_packages from definition: {pre_installed}")
        else:
            # Priority 2: Fallback to library.json golden_images
            meta = self._load_library_metadata().get("_meta", {})
            golden = meta.get("golden_images", {})
            
            image_tag = base_rule.get('image')
            if image_tag in golden:
                pre_installed = set(golden[image_tag].get("pre_installed", []))
                if pre_installed:
                    print(f"[Golden Image] Using pre_installed from library.json for '{image_tag}': {pre_installed}")
        
        if not pre_installed:
            return packages, []  # Return tuple with empty removed list
        
        # Create normalized lookup for pre-installed packages
        normalized_installed = {normalize_pkg_name(pkg): pkg for pkg in pre_installed}
        
        # Filter out packages that are already installed
        # Need to extract base package name for comparison
        filtered = []
        removed = []
        conflicts = []  # Track version conflicts
        
        for pkg in packages:
            pkg_name = pkg.split('==')[0].split('>=')[0].split('<=')[0].strip()
            
            # Check both exact and normalized match
            is_installed = False
            matched_name = None
            
            if pkg_name in pre_installed:
                is_installed = True
                matched_name = pkg_name
            else:
                # Try normalized match
                normalized = normalize_pkg_name(pkg_name)
                if normalized in normalized_installed:
                    is_installed = True
                    matched_name = normalized_installed[normalized]
            
            if is_installed:
                # Check for version conflict
                if '==' in pkg or '>=' in pkg or '<=' in pkg:
                    # User is trying to install specific version of already-installed package
                    conflicts.append(pkg)
                removed.append(matched_name)  # Store the matched installed name
            else:
                filtered.append(pkg)
        
        if removed:
            print(f"\n[Excluded - Pre-installed] The following {len(removed)} package(s) are already in the base image '{base_rule.get('id', 'unknown')}' and will NOT be reinstalled:")
            for pkg in removed:
                print(f"  ✗ {pkg} (already in Layer 2)")
            print()
        
        if conflicts:
            print(f"[WARNING] Version conflicts detected! Attempting to override stable Layer 2 packages: {', '.join(conflicts)}")
            print(f"[WARNING] Recommendation: Remove these from your custom environment to avoid breaking the base image.")
        
        return filtered, removed  # Return tuple

    
    def validate_environment(self):
        """
        Check if Docker is available and running.
        
        Raises:
            DockerUnavailableError: If Docker is not found or not running.
        """
        try:
            # lightweight check
            subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise DockerUnavailableError("Docker is not running or not installed. Please start Docker Desktop.")

    def get_available_runtimes(self) -> List[ImageRule]:
        """Return list of available runtimes from rules."""
        return self.IMAGE_RULES

    def resolve_runtime(self, search_terms, version_hint: str = "unknown") -> ImageRule:
        """
        Resolve best runtime based on search terms (keywords/libs) and version.
        Replaces 'select_image' with more robust matching.
        
        Args:
            search_terms: Either List[str] of search terms, or Dict (analysis result)
            version_hint: Version string (optional if search_terms is a dict)
        
        CRITICAL: Major version (2.x vs 3.x) compatibility is the PRIMARY criterion.
        Images with incompatible major versions receive overwhelming penalties.
        """
        # Handle both list and dict inputs for backward compatibility
        if isinstance(search_terms, dict):
            # Dict format: extract info from analysis result
            version_hint = search_terms.get('version', 'unknown')
            libs = search_terms.get('libraries', search_terms.get('imports', []))
            keywords = search_terms.get('keywords', [])
            terms_set = set(libs + keywords)
        else:
            # List format: use as-is
            terms_set = set(search_terms)
        
        best_rule = self.IMAGE_RULES[-1]  # Default to latest 3.x
        best_score = -999999  # Very low default to allow penalties
        best_reasons = []
        
        # Scoring details for each rule
        scoring_log = []

        for rule in self.IMAGE_RULES:
            # Extract major version from both code and rule
            code_major = self._get_major_version(version_hint)
            rule_major = self._get_major_version(rule['version'])
            
            # 1. CRITICAL: Major Version Compatibility Check
            # Apply overwhelming penalty if major versions are incompatible
            score = 0
            reasons = []
            
            if code_major != 'unknown' and rule_major != 'unknown':
                if code_major == rule_major:
                    # Same major version: huge bonus (overrides all other factors)
                    score += 10000
                    reasons.append(f"Major version match (Python {code_major}.x)")
                else:
                    # Different major version: massive penalty (makes this rule almost impossible to select)
                    score -= 100000
                    reasons.append(f"INCOMPATIBLE: Code needs Python {code_major}.x, image provides {rule_major}.x")
            elif code_major == 'unknown' or rule_major == 'unknown':
                # Unknown version: neutral (no bonus/penalty)
                reasons.append("Version unknown - neutral scoring")
                
            # 2. Exact Version Match Bonus (secondary to major version)
            if version_hint != 'unknown' and rule['version'] == version_hint:
                score += 500
                reasons.append(f"Exact version match ({version_hint})")
            
            # 3. Library/Keyword Matching (tertiary)
            rule_libs = set(rule.get('libs', []))
            rule_triggers = set(rule.get('triggers', []))
            all_criteria = rule_libs.union(rule_triggers)
            
            if all_criteria:
                matched = all_criteria.intersection(terms_set)
                missing = rule_libs - terms_set  # Only penalize missing 'required' libs
                
                if matched:
                    score += len(matched) * 20
                    reasons.append(f"Matched libraries: {', '.join(matched)}")
                
                if missing:
                    score -= len(missing) * 10
                    reasons.append(f"Missing libraries: {', '.join(missing)}")
                
                # Bonus for trigger match
                if rule_triggers.intersection(terms_set):
                    score += 30
                    reasons.append("Trigger keywords matched")
            
            scoring_log.append({
                'rule': rule['id'],
                'score': score,
                'reasons': reasons
            })
            
            if score > best_score:
                best_score = score
                best_rule = rule.copy()  # Copy to avoid mutating original
                best_reasons = reasons.copy()
        
        # Add reasoning to the returned rule
        best_rule['reason'] = " | ".join(best_reasons) if best_reasons else "Default selection"
        best_rule['score'] = best_score
        
        # Log scoring details for debugging
        print(f"\n[ContainerManager] Runtime Selection for Python {version_hint}:")
        for log in scoring_log:
            print(f"  - {log['rule']}: Score={log['score']} | {' | '.join(log['reasons'])}")
        print(f"  => SELECTED: {best_rule['id']} (Score: {best_score})")
        print(f"  => REASON: {best_rule['reason']}\n")
                
        return best_rule
    
    def _get_major_version(self, version_str: str) -> str:
        """
        Extract major version from version string.
        
        Args:
            version_str: Version string like "2.7", "3.x", "3.10", "unknown"
            
        Returns:
            Major version as "2" or "3", or "unknown"
        """
        if not version_str or version_str == 'unknown':
            return 'unknown'
            
        # Handle "3.x" format
        if version_str.startswith('3'):
            return '3'
        elif version_str.startswith('2'):
            return '2'
        else:
            return 'unknown'
        
    def _check_version_compat(self, code_ver, rule_ver):
        if code_ver == 'unknown' or rule_ver == 'unknown': return True
        if code_ver == rule_ver: return True
        if code_ver == '3.x' and rule_ver.startswith('3'): return True
        if code_ver.startswith('3') and rule_ver == '3.x': return True
        return False

    def select_image(self, analysis_result: AnalysisResult) -> ImageRule:
        """Legacy wrapper for backward compatibility."""
        # Convert analysis result to search terms
        libs = analysis_result.get('libraries', [])
        keywords = analysis_result.get('keywords', [])
        version = analysis_result.get('version', 'unknown')
        
        search_terms = libs + keywords
        return self.resolve_runtime(search_terms, version)
    
    def prepare_run_config(
        self, 
        analysis_result: AnalysisResult, 
        script_path: str,
        work_dir: Optional[str] = None,
        data_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        override_image_rule: Optional[ImageRule] = None
    ) -> RunConfig:
        """
        Prepare Docker run configuration with separate input/output mounts.
        Supports manual override of the image selection.
        """
        import datetime
        
        # Select image rule
        if override_image_rule:
            rule = override_image_rule
            # Compatibility Check (Warning Log)
            detected_ver = analysis_result.get('version', 'unknown')
            rule_ver = rule.get('version', 'unknown')
            if not self._check_version_compat(detected_ver, rule_ver):
                print(f"[RunConfig] WARNING: Version mismatch detected! Code: {detected_ver}, Image: {rule_ver}")
        else:
            rule = self.select_image(analysis_result)
            
        image = rule['image']
        
        # Logic to check if we should prepend python
        # 1. Use explicit rule setting if present
        # 2. If valid LCR image (constructed via template), ENTRYPOINT is python, so don't prepend
        if 'prepend_python' in rule:
            prepend_python = rule['prepend_python']
        else:
            # Auto-detection: If image starts with 'lcr-', assume it has ENTRYPOINT ["python"]
            prepend_python = not image.startswith('lcr-')
        
        # Determine paths
        script_path_obj = Path(script_path).resolve()
        if not script_path_obj.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        # 1. Host Input Directory (Source for Script) -> /app/input (RO)
        # We assume the script is in a directory that serves as its "input context".
        host_input_dir = script_path_obj.parent
        script_name = script_path_obj.name
        
        # 2. Host Output Directory -> /app/output (RW)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        sub_dir_name = f"LCR_RUN_{timestamp}"
        
        if output_dir:
            # User specified path
            base_output_path = Path(output_dir).resolve()
            
            # Safety Check: Collision with Input
            # We strictly prevent outputting directly into the source directory to avoid clutter/overwrites
            # unless it's a dedicated results folder within it (handled by subfolder logic)
            if base_output_path == host_input_dir:
                raise ValueError(
                    f"Output directory cannot be identical to the script source directory: {host_input_dir}. "
                    "Please select a different folder."
                )
                
            host_output_dir = base_output_path / sub_dir_name
        else:
            # Default logic: {ProjectRoot}/data/results/{YYYYMMDD_HHMMSS}
            # Inferred Project Root: 4 levels up
            project_root = Path(__file__).resolve().parents[4]
            
            # Fallback if project root seems wrong
            if not (project_root / "run_gui.py").exists() and not (project_root / ".git").exists():
                 project_root = Path.cwd()
            
            host_output_dir = project_root / "data" / "results" / timestamp
        
        # Create output directory
        host_output_dir.mkdir(parents=True, exist_ok=True)
        
        # --- SNAPSHOT SAFETY FEATURE ---
        # Copy the source script to the output directory as 'source_snapshot.py'.
        # This ensures auditability even if the original script is modified later.
        try:
            import shutil
            snapshot_path = host_output_dir / "source_snapshot.py"
            shutil.copy2(script_path, snapshot_path)
        except Exception as e:
            # Non-blocking failure: Log warning but proceed with execution
            print(f"[Warning] Failed to create source snapshot: {e}")
        # -------------------------------
        
        # Container Paths
        container_input_dir = '/app/input'
        container_output_dir = '/app/output'
        container_script_path = f'{container_input_dir}/{script_name}'
        
        # Build volumes
        volumes = {
            # Script Input (Read-only)
            str(host_input_dir): {
                'bind': container_input_dir,
                'mode': 'ro' 
            },
            # Result Output (Read-write)
            str(host_output_dir): {
                'bind': container_output_dir,
                'mode': 'rw'
            }
        }
        
        # Add optional data volume if provided (e.g., large datasets)
        if data_dir:
            host_data_dir = Path(data_dir).resolve()
            if host_data_dir.exists():
                volumes[str(host_data_dir)] = {
                    'bind': '/data',
                    'mode': 'ro' 
                }
        
        # Build configuration
        # Handle Entrypoint logic
        if prepend_python:
            command = ['python', container_script_path]
        else:
            command = [container_script_path]
            
        config: RunConfig = {
            'image': image,
            'volumes': volumes,
            # Set working dir to output so artifacts land there
            'working_dir': container_output_dir, 
            'command': command,
            'script_name': script_name,
            'host_work_dir': str(host_output_dir), # Reported host work dir matches output
        }
        
        return config
    
    def get_docker_run_args(self, config: RunConfig) -> list:
        """
        Convert configuration to docker run command arguments.
        
        Args:
            config: Configuration from prepare_run_config()
        
        Returns:
            List of command arguments for subprocess
        """
        args = ['docker', 'run', '--rm']
        
        # Add volume mounts
        for host_path, mount_config in config['volumes'].items():
            bind_path = mount_config['bind']
            mode = mount_config.get('mode', 'rw')
            args.extend(['-v', f'{host_path}:{bind_path}:{mode}'])
        
        # Add working directory
        args.extend(['-w', config['working_dir']])
        
        # Add image
        args.append(config['image'])
        
        # Add command
        args.extend(config['command'])
        
        return args
    
    def install_dependencies(
        self, 
        analysis_result: Dict,
        requirements_file: Optional[str] = None
    ) -> Optional[list]:
        """
        Generate pip install commands for detected libraries.
        
        This is a future extension point for automatic dependency installation.
        
        Args:
            analysis_result: Dictionary from CodeAnalyzer.summary()
            requirements_file: Optional path to requirements.txt
        
        Returns:
            List of pip install commands, or None if no dependencies
        """
        libraries = analysis_result.get('libraries', [])
        
        if not libraries:
            return None
        
        # Filter out standard library modules
        # This is a simplified approach - could be enhanced with stdlib detection
        external_libs = [lib for lib in libraries if lib not in ['sys', 'os', 're', 'json']]
        
        if not external_libs:
            return None
        
        # Generate pip install command
        # Note: This is a placeholder for future enhancement
        # In practice, you'd want to handle version pinning, etc.
        pip_cmd = ['pip', 'install'] + external_libs
        
        return [pip_cmd]

    def synthesize_definition_config(self, analysis_result: Dict, base_rule_id: str) -> Dict:
        """
        Create a new environment configuration based on analysis and a selected base image.
        
        Args:
            analysis_result: Result from CodeAnalyzer
            base_rule_id: ID of the base image rule to extend
            
        Returns:
            Dict containing the new definition config (ready for JSON save)
        """
        # Find base rule
        base_rule = next((r for r in self.IMAGE_RULES if r['id'] == base_rule_id), None)
        if not base_rule:
            # Fallback to latest python
            base_rule = self.IMAGE_RULES[-1]
        
        print(f"[synthesize_definition_config] Using base_rule: {base_rule['id']}, installed_packages: {base_rule.get('installed_packages', [])}")
            
        # --- [Lazy Hydration] 既設パッケージリストが空の場合の救済措置 ---
        installed = set(base_rule.get('installed_packages', []))

        # もしリストが空で、かつベースイメージが既知のGolden Imageである場合
        if not installed:
            base_image = base_rule.get('base_image') or base_rule.get('image', '')
            # 既知のゴールデン・イメージ (py36-ds等) を探す
            # self.IMAGE_RULES (ハードコード/ライブラリ定義) から、同じイメージを使う親ルールを探す
            parent_rule = next((r for r in self.IMAGE_RULES 
                                if r.get('image') == base_image and r.get('installed_packages')), None)
            
            if parent_rule:
                installed = set(parent_rule.get('installed_packages', []))
                print(f"[Info] Hot-fixed missing packages for '{base_rule['id']}' using parent '{parent_rule['id']}'")
                
                # Apply to base_rule for downstream usage (diff calculation, etc.)
                base_rule = base_rule.copy()
                base_rule['installed_packages'] = list(installed)
        # ----------------------------------------------------------------

        # 1. Resolve Detected Packages to Pip/Apt names
        from lcr.core.detector.analyzer import CodeAnalyzer
        # We need an instance to access the loaded mappings
        # Pass our loaded metadata (with overlays) to the analyzer
        analyzer = CodeAnalyzer(mappings=self._load_library_metadata()) 
        detected_imports = analysis_result.get('libraries', [])
        resolved = analyzer.resolve_packages(detected_imports)
        
        detected_pip = set(resolved['pip'])
        detected_apt = set(resolved['apt'])
        
        # 2. Extract version from base rule for legacy pins
        version = self._extract_version(base_rule)
        
        # 3. Subtract packages pre-installed in golden images
        # This uses installed_packages field synced from library.json
        # Returns tuple: (filtered_packages, removed_packages)
        needed_pip, skipped_packages = self._subtract_golden_packages(list(detected_pip), base_rule)
        
        # 4. Then apply legacy version pins if applicable
        if version:
            needed_pip = self._apply_legacy_pins(needed_pip, version)
                 
        # 5. Construct Config with Layer Inheritance
        # Copy installed_packages from base rule so Layer 3 remembers Layer 2 contents
        base_installed = base_rule.get('installed_packages', [])
        
        # Combine Layer 2 packages with newly installed packages for Layer 3 definition
        # This ensures that if Layer 3 becomes a base for Layer 4, the full package list is known
        new_installed_packages = base_installed.copy() if isinstance(base_installed, list) else list(base_installed)
        
        # Add the packages we're about to install to the installed_packages list
        # This way, Layer 3's definition will have the complete list of what's inside it
        for pkg in needed_pip:
            # Extract package name without version spec
            pkg_name = pkg.split('==')[0].split('>=')[0].split('<=')[0].strip()
            if pkg_name not in new_installed_packages:
                new_installed_packages.append(pkg_name)
        
        # Log the inheritance and accumulation
        if base_installed:
            print(f"\n[Layer Inheritance] New environment (Layer 3) inherits {len(base_installed)} package(s) from base '{base_rule['id']}' (Layer 2):")
            for pkg in base_installed:
                print(f"  ← {pkg}")
        
        if needed_pip:
            print(f"\n[New Installations] Layer 3 will install {len(needed_pip)} additional package(s):")
            for pkg in needed_pip:
                print(f"  + {pkg}")
        
        if new_installed_packages:
            print(f"\n[Total Package Inventory] Layer 3 will contain {len(new_installed_packages)} package(s) total.")
            print()
        
        # Fetch global pip config if available (e.g. from enterprise.json)
        full_lib_data = self._load_library_metadata()
        meta = full_lib_data.get("_meta", {})
        pip_config = meta.get("pip_config", {})

        config = {
            "tag": "custom-auto-gen", # Placeholder, user should override
            "base_image": base_rule.get('image', 'python:3.10-slim'),
            "apt_packages": list(detected_apt),
            "pip_packages": needed_pip,
            "installed_packages": new_installed_packages,  # Full inventory: Layer 2 + Layer 3 additions
            "pip_config": pip_config, # Private Registry Settings
            "env_vars": {"PYTHONUNBUFFERED": "1"},
            "run_commands": [],
            "_resolution_reasons": resolved.get("reasons", {}), # Metadata for UI
            "_unresolved": list(resolved.get("unresolved", [])), # Metadata for UI
            "_skipped_packages": skipped_packages, # Packages excluded (Layer 2)
            "_skipped_reason": "Pre-installed in base image (Layer 2)"
        }
        
        return config

    def get_build_command(self, dockerfile_path: str, tag: str) -> list:
        """Construct docker build command."""
        # Use absolute path for safety
        path_obj = Path(dockerfile_path).resolve()
        context_dir = path_obj.parent
        
        return [
            "docker", "build",
            "-t", tag,
            "-f", str(path_obj),
            str(context_dir)
        ]
