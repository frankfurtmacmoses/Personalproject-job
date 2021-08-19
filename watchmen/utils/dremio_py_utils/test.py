import common_utils as cu
import dremio_utils as du
import argparse

def main(args):
	secret_dict = cu.get_secret(args.dremio_secret, "us-east-1")
	print(secret_dict)
	return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="curate a file of dns", allow_abbrev=True)
    parser.add_argument('--dremio_secret', '-ds', help="Secret key of Dremio auth stored in Secret manager", required=True)
    parser.add_argument('--dremio_secret_key', '-dsk', help="Dictionary key value of the secret dict returned from Secret manager", required=False)
    args = parser.parse_args()
    main(args)