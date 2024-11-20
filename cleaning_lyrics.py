import csv
import re
import ftfy

def clean_lyrics(lyrics):
    """
    Cleans the lyrics by:
    - Fixing encoding issues using ftfy.
    - Removing any text before and including 'Lyrics' or similar markers.
    - Removing any trailing metadata like 'You might also like' or 'Embed'.
    - Removing all words enclosed in square brackets, e.g., [Verse 1], [Chorus].
    - Removing extra whitespace.

    Parameters:
    - lyrics: str, the original lyrics text.

    Returns:
    - cleaned_lyrics: str, the cleaned lyrics text.
    """
    # Fix text encoding issues using ftfy
    lyrics = ftfy.fix_text(lyrics)

    # Remove everything before and including the word 'Lyrics' (case-insensitive)
    lyrics = re.sub(r'^.*?\blyrics\b', '', lyrics, flags=re.IGNORECASE | re.DOTALL).strip()

    # Remove everything after 'You might also like', 'Embed', or any trailing numbers
    lyrics = re.split(r'\bYou might also like\b|\bEmbed\b|\d+Embed', lyrics, flags=re.IGNORECASE)[0].strip()

    # Remove all text enclosed in square brackets, including the brackets
    lyrics = re.sub(r'\[.*?\]', '', lyrics)

    # Remove extra whitespace
    lyrics = re.sub(r'\s+', ' ', lyrics).strip()

    return lyrics

def clean_lyrics_in_csv(input_csv, output_csv):
    """
    Reads the input CSV file, cleans the lyrics column, and writes the cleaned data to the output CSV file.

    Parameters:
    - input_csv: str, path to the input CSV file.
    - output_csv: str, path to the output CSV file where cleaned data will be saved.
    """
    try:
        # Set the CSV field size limit to the maximum value for a 32-bit signed integer
        max_field_size = 2147483647  # 2 GB
        csv.field_size_limit(max_field_size)

        with open(input_csv, mode='rb') as infile, \
             open(output_csv, mode='w', encoding='utf-8', newline='') as outfile:

            # Read the file in binary mode and decode lines as UTF-8, replacing invalid characters
            decoded_lines = (line.decode('utf-8', 'replace') for line in infile)

            reader = csv.reader(decoded_lines)
            writer = csv.writer(outfile)

            # Read the header and write it to the output file
            header = next(reader)
            writer.writerow(header)

            # Get the index of the lyrics column
            try:
                lyrics_index = header.index('lyrics')
            except ValueError:
                print("Error: 'lyrics' column not found in the CSV header.")
                return

            for row_number, row in enumerate(reader, start=2):
                if len(row) <= lyrics_index:
                    print(f"Warning: Row {row_number} does not have enough columns. Skipping.")
                    continue

                lyrics = row[lyrics_index]

                # Clean the lyrics
                cleaned_lyrics = clean_lyrics(lyrics)

                # Update the lyrics column in the row
                row[lyrics_index] = cleaned_lyrics

                # Write the updated row to the output file
                writer.writerow(row)

        print(f"Cleaned lyrics have been written to '{output_csv}'.")

    except FileNotFoundError:
        print(f"Error: The file '{input_csv}' does not exist.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Usage example
if __name__ == "__main__":
    input_csv_file = 'songs_data.csv'          # Replace with your input CSV file name/path
    output_csv_file = 'cleaned_lyrics.csv'     # The output CSV file with cleaned lyrics

    clean_lyrics_in_csv(input_csv_file, output_csv_file)
