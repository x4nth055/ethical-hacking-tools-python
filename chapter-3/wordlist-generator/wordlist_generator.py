import argparse
import itertools
import string
import time
import sys
from typing import Iterator

class WordlistGenerator:
    """
    A flexible and sophisticated word list generator.
    """
    def __init__(self):
        self.charset = ""
        self.min_length = 1
        self.max_length = 8
        self.pattern = None
        self.output_file = None

    def generate_wordlist(self) -> Iterator[str]:
        """
        Generate the word list based on the specified parameters.
        
        Returns:
            Iterator[str]: An iterator of generated words.
        """
        if self.pattern:
            yield from self._generate_with_pattern()
        else:
            yield from self._generate_without_pattern()

    def _generate_with_pattern(self) -> Iterator[str]:
        """
        Generate words based on a specified pattern.
        
        Returns:
            Iterator[str]: An iterator of generated words matching the pattern.
        """
        pattern_chars = list(self.pattern)
        for i, char in enumerate(pattern_chars):
            if char == '@':
                pattern_chars[i] = string.ascii_lowercase
            elif char == ',':
                pattern_chars[i] = string.ascii_uppercase
            elif char == '%':
                pattern_chars[i] = string.digits
            elif char == '^':
                pattern_chars[i] = string.punctuation

        for word in itertools.product(*pattern_chars):
            yield ''.join(word)

    def _generate_without_pattern(self) -> Iterator[str]:
        """
        Generate words without a specific pattern.
        
        Returns:
            Iterator[str]: An iterator of generated words.
        """
        for length in range(self.min_length, self.max_length + 1):
            for word in itertools.product(self.charset, repeat=length):
                yield ''.join(word)

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Sophisticated Word List Generator")
    parser.add_argument("-c", "--charset", type=str, help="Custom character set")
    parser.add_argument("-m", "--min", type=int, default=1, help="Minimum word length")
    parser.add_argument("-M", "--max", type=int, default=8, help="Maximum word length")
    parser.add_argument("-p", "--pattern", type=str, help="Pattern for word generation")
    parser.add_argument("-o", "--output", type=str, help="Output file")
    parser.add_argument("-l", "--lowercase", action="store_true", help="Include lowercase letters")
    parser.add_argument("-u", "--uppercase", action="store_true", help="Include uppercase letters")
    parser.add_argument("-d", "--digits", action="store_true", help="Include digits")
    parser.add_argument("-s", "--special", action="store_true", help="Include special characters")
    
    return parser.parse_args()

def main():
    """
    Main function to run the word list generator.
    """
    args = parse_arguments()
    generator = WordlistGenerator()

    # Set up pattern
    generator.pattern = args.pattern
    # Set up character set
    if args.charset:
        generator.charset = args.charset
    else:
        if args.lowercase:
            generator.charset += string.ascii_lowercase
        if args.uppercase:
            generator.charset += string.ascii_uppercase
        if args.digits:
            generator.charset += string.digits
        if args.special:
            generator.charset += string.punctuation

    if not generator.charset and generator.pattern is None:
        print("[!] Error: No character set specified or pattern not provided. Use -h for help.")
        sys.exit(1)

    # Set up other parameters
    generator.min_length = args.min
    generator.max_length = args.max
    generator.output_file = args.output

    # Generate and output words
    output = open(generator.output_file, 'w') if generator.output_file else sys.stdout
    t = time.time()
    try:
        for word in generator.generate_wordlist():
            print(word, file=output)
    finally:
        if output != sys.stdout:
            output.close()
    if generator.output_file:
        print(f"[+] Word list saved to {generator.output_file}.")
        print(f"[+] Word list generated in {time.time() - t:.2f} seconds.")
        n_words = open(generator.output_file).read().count('\n')
        print(f"[+] Total words generated: {n_words}")

if __name__ == "__main__":
    main()
