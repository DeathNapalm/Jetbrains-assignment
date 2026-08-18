{
  description = "AWS Terraform K6 Load Testing Development Environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Terraform
            terraform

            # AWS CLI
            awscli2

            # Docker
            docker
            docker-compose

            # K6 Load Testing
            k6

            # Additional utilities
            git
            curl
            jq
            openssh
          ];

          shellHook = ''
            echo "🚀 AWS Terraform K6 Development Environment"
            echo "Available tools:"
            echo "  - terraform"
            echo "  - aws"
            echo "  - docker"
            echo "  - docker-compose"
            echo "  - k6"
          '';
        };
      }
    );
}
