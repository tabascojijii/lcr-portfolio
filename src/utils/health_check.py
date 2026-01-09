import docker
import sys

def check_docker_environment():
    """
    ホストPCのDocker環境をチェックし、ステータスを表示する。
    """
    print("--- LCR Environment Health Check ---")
    
    try:
        # Docker クライアントの初期化 (環境変数から自動設定)
        client = docker.from_env()
        
        # 疎通確認
        if client.ping():
            version_info = client.version()
            print("✅ Docker is running!")
            print(f"   - Version: {version_info.get('Version')}")
            print(f"   - OS: {version_info.get('Os')}")
            print(f"   - Architecture: {version_info.get('Arch')}")
            
            # 既存のイメージ一覧を軽く取得して権限チェック
            images = client.images.list()
            print(f"   - Local Images: {len(images)} images found.")
            
            return True
        else:
            print("⚠️  Docker responded to ping, but something is wrong.")
            return False

    except docker.errors.DockerException as e:
        print("❌ Error: Cannot connect to Docker.")
        print(f"   Details: {e}")
        print("\nPossible fixes:")
        print("1. Make sure Docker Desktop is running.")
        print("2. (Windows) Ensure 'Expose daemon on tcp://localhost:2375 without TLS' is NOT needed if using default pipes.")
        print("3. Check if your user has permission to access the Docker socket.")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    success = check_docker_environment()
    print("-" * 36)
    if success:
        print("Result: READY to develop LCR.")
        sys.exit(0)
    else:
        print("Result: SETUP REQUIRED.")
        sys.exit(1)