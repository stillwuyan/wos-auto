import argparse
import utils
import test
import process

if __name__ == '__main__':
    parser = argparse.ArgumentParser('python main.py')
    parser.add_argument('-i', '--interval', type=float, default=1.0, help='Set cycle interval (seconds)')
    parser.add_argument('-s', '--source', type=str, default='adb', choices=['adb', 'net'], help='Choose source')
    parser.add_argument('-m', '--mime', type=str, default='raw', choices=['raw', 'img'], help='Choose media type')
    parser.add_argument('-t', '--target', type=str, default='s20', choices=['s20', 'note4'], help='Choose target')

    sub_parser = parser.add_subparsers(dest='command')
    parser_test = sub_parser.add_parser('test', help='Test command')
    parser_test.add_argument('-a', '--action', type=str, default='all', help='Choose action',
                             choices=['all', 'help', 'chat', 'heal', 'capture', 'display', 'conv'])
    parser_test.add_argument('-s', '--source', type=str, default='adb', choices=['adb', 'net'], help='Choose source')
    parser_test.add_argument('-m', '--mime', type=str, default='raw', choices=['raw', 'img'], help='Choose media type')
    parser_test.add_argument('-t', '--target', type=str, default='s20', help='Choose target',
                             choices=['s20', 'note4', 'mini'])
    parser_test.add_argument('-f', '--file', type=str, help='Set input file')

    args = parser.parse_args()
    inner_source = utils.source_name(args.source, args.mime)
    if args.command == 'test':
        match args.action:
            case 'all':
                test.all(inner_source, args.target)
                exit(0)
            case 'capture':
                file = test.capture(inner_source)
                print(file)
                exit(0)

        if args.file is None:
            print('Need set the input file')
            exit(0)

        match args.action:
            case 'display':
                test.display(args.file, inner_source)
            case 'conv':
                test.conv(args.file)
            case 'help':
                test.help(args.file, inner_source, args.target)
            case 'chat':
                test.chat(args.file, inner_source, args.target)
            case 'heal':
                test.heal(args.file, inner_source, args.target)
    else:
        proc = process.Proc(inner_source, args.target, args.interval)
        proc.run()