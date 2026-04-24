{
  description = "DevForge 開発環境";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # WeasyPrint が必要とするネイティブライブラリ
        weasyPrintLibs = with pkgs; [
          pango
          cairo
          glib
          gobject-introspection
          libffi
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            # --- Python (Backend) ---
            python313          # Python 3.13（Dockerfile 準拠）
            uv                 # 高速パッケージマネージャ

            # --- Node.js (Frontend) ---
            nodejs_22          # Node.js 22 LTS
            nodePackages.npm

            # --- WeasyPrint ネイティブ依存 ---
            pango
            cairo
            glib
            gobject-introspection
            libffi
            fontconfig
            freetype

            # --- ミドルウェア ---
            redis              # Redis 7（ローカル開発用）

            # --- 共通ツール ---
            git
            curl
            gnumake
          ];

          # WeasyPrint が共有ライブラリを発見できるよう LD_LIBRARY_PATH を設定
          shellHook = ''
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath weasyPrintLibs}:$LD_LIBRARY_PATH"

            # uv が Python 3.13 を使うよう明示
            export UV_PYTHON="${pkgs.python313}/bin/python3"

            echo ""
            echo "DevForge 開発環境"
            echo "  Python : $(python3 --version)"
            echo "  Node   : $(node --version)"
            echo "  uv     : $(uv --version)"
            echo "  Redis  : $(redis-server --version)"
            echo ""
            echo "セットアップ: make setup"
            echo ""
          '';
        };
      }
    );
}
