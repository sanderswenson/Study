import os

# Paths to the uploaded files
file_paths = [
    r'C:\Users\Epicp\Documents\The Notebook\Nootropics\GPT\Pleasantness.md',
    r'C:\Users\Epicp\Documents\The Notebook\Nootropics\GPT\Antianxiety.md',
    r'C:\Users\Epicp\Documents\The Notebook\Nootropics\GPT\Focus.md',
    r'C:\Users\Epicp\Documents\The Notebook\Nootropics\GPT\Memory.md',
    r'C:\Users\Epicp\Documents\The Notebook\Nootropics\GPT\Motivation.md',
    r'C:\Users\Epicp\Documents\The Notebook\Nootropics\GPT\Mood.md'
]

# Function to read the contents of each file
def read_md_file(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()

def filter_lines(lines):
    top_lines = []
    for line in lines:
        if "Below Moderate" in line:
            break
        top_lines.append(line.strip())
    return top_lines

def unique_lines(lines):
    seen = set()
    unique = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return unique

for path in file_paths:
    filtered_lines = []
    filtered_unique_lines = []
    
    #Get all the lines from file until Below Moderate
    for path in file_paths:
        all_lines = []
        all_lines.extend(read_md_file(path))
        #Append to array
        filtered_lines += filter_lines(all_lines)
        

    #Name duplicates
    filtered_unique_lines = unique_lines(filtered_lines)


# Write the final list to a new markdown file
output_path = r'C:\Users\Epicp\Documents\The Notebook\Nootropics\GPT\Final_Filtered2.md'
with open(output_path, 'w') as file:
    file.write("# Nootropics Above Below Moderate\n\n")
    for line in filtered_unique_lines:
        file.write(f"{line}\n")

print(f"Filtered data written to: {output_path}")
