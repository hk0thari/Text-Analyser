import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import unicodedata

from web_scraper import download_books

# Uncomment this to start downloading books
# Don't need to do this anymore, since I already let this run for long enough for a lot of books
#download_books()


def analyse_text(text: str):
    text = text.lower()

    counts = {}
    for character in text:
        category = unicodedata.category(character)
        if category.startswith("L"):
            counts[character] = counts.get(character, 0) + 1

    total_length = sum(counts.values())
    for character, occurrence in counts.items():
        counts[character] = int(occurrence/total_length*10000)/100

    sorted_counts = dict(sorted(counts.items(), key=lambda x:x[1], reverse=True))
    return sorted_counts


def analyse_author(path):
    books = os.listdir(path)

    merged = ""
    error_list = []

    for book in books:
        try:
            with open(os.path.join(path, book), mode='r', encoding='utf-8-sig') as b:
                merged += b.read()
        except Exception as e:
            error_list.append(e)
            print(path, book)

    if error_list:
        print(error_list)

    statistics = analyse_text(merged)

    return statistics


def analyse_all_books():
    """Analyse all books once and cache results"""

    print("Analyzing all books (this will take a moment...")

    all_stats = {}  # Cache for all analysis results
    language_texts = defaultdict(str)  # Combined text per language

    languages = os.listdir("Books")

    for language in languages:
        print(f"\nProcessing language: {language}\n")
        language_path = os.path.join("Books", language)
        authors = os.listdir(language_path)

        all_stats[language] = {}

        for author in authors:
            print(f"  Processing author: {author}")
            author_path = os.path.join(language_path, author)
            books = os.listdir(author_path)

            author_text = ""
            error_list = []

            for book in books:
                try:
                    with open(os.path.join(author_path, book), mode='r', encoding='utf-8-sig') as f:
                        book_content = f.read()
                        author_text += book_content
                        language_texts[language] += book_content
                except Exception as e:
                    error_list.append(e)
                    print(f"    Error reading {book}: {e}")

            if error_list:
                print(f"    {len(error_list)} errors for {author}")

            # Analyze author's combined text once
            all_stats[language][author] = analyse_text(author_text)

    # Analyze language-level text once
    language_stats = {}
    for language, combined_text in language_texts.items():
        print(f"Analyzing combined text for language: {language}")
        language_stats[language] = analyse_text(combined_text)

    print("Analysis complete!")
    return all_stats, language_stats


def generate_author_statistics_df(language, author_stats):
    """Generate a pandas DataFrame with author statistics from cached results"""

    data = []

    for author, statistics in author_stats.items():
        # Get top 10 characters for better analysis
        top_chars = list(statistics.items())[:10]

        row_data = {'Author': author}
        for i, (char, freq) in enumerate(top_chars):
            row_data[f'Char_{i+1}'] = char
            row_data[f'Freq_{i+1}'] = freq

        # Only store top 20 characters to reduce memory usage
        for char, freq in list(statistics.items())[:20]:
            row_data[f'char_{char}'] = freq

        data.append(row_data)

    return pd.DataFrame(data)


def generate_language_statistics(all_stats, language_stats):
    """Generate comprehensive statistics from cached results"""

    language_dfs = {}
    all_language_data = []

    for language in all_stats.keys():
        print(f"Generating DataFrame for language: {language}")

        # Generate author statistics for this language using cached data
        df = generate_author_statistics_df(language, all_stats[language])
        df['Language'] = language
        language_dfs[language] = df

        # Use cached language-level statistics
        lang_stats = language_stats[language]
        lang_row = {'Language': language}
        for char, freq in lang_stats.items():
            lang_row[f'char_{char}'] = freq
        all_language_data.append(lang_row)

    # Create language comparison DataFrame
    language_comparison_df = pd.DataFrame(all_language_data)

    return language_dfs, language_comparison_df


def save_statistics_to_csv(language_dfs, language_comparison_df):
    """Save all statistics to CSV files"""

    # Save individual language statistics
    for language, df in language_dfs.items():
        filename = f"statistics_{language.lower()}.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {language} statistics to {filename}")

    # Save language comparison
    language_comparison_df.to_csv("language_comparison.csv", index=False, encoding='utf-8')
    print("Saved language comparison to language_comparison.csv")

    # Save combined statistics
    combined_df = pd.concat(language_dfs.values(), ignore_index=True)
    combined_df.to_csv("all_statistics.csv", index=False, encoding='utf-8')
    print("Saved combined statistics to all_statistics.csv")


def visualize_author_comparison(language_dfs):
    """Create visualizations comparing authors within each language"""

    for language, df in language_dfs.items():
        # Create simplified 1x2 subplot layout to reduce crowding
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(f'Character Frequency Analysis - {language}', fontsize=16)

        # 1. Heatmap of top characters by author (limit authors displayed if too many)
        char_cols = [col for col in df.columns if col.startswith('char_')]
        if char_cols:
            # Get top 10 most common characters across all authors
            char_means = df[char_cols].mean().sort_values(ascending=False)[:10]
            top_chars = char_means.index

            # Limit to top 15 authors if more than 15 to avoid crowding
            df_display = df.head(15) if len(df) > 15 else df

            heatmap_data = df_display.set_index('Author')[top_chars]
            sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[0],
                        cbar_kws={'shrink': 0.8})
            axes[0].set_title('Top 10 Characters by Author (%)')
            axes[0].set_xlabel('Characters')

            if len(df) > 15:
                axes[0].set_xlabel(f'Characters (showing top 15 of {len(df)} authors)')

        # 2. Bar plot of most frequent characters (average across authors)
        if len(char_means) > 0:
            top_10_chars = char_means[:10]
            # Clean character names for display
            char_names = [col.replace('char_', '') for col in top_10_chars.index]
            axes[1].bar(char_names, top_10_chars.values, color='skyblue', alpha=0.7)
            axes[1].set_title(f'Top 10 Characters - {language} (Average)')
            axes[1].set_xlabel('Characters')
            axes[1].set_ylabel('Frequency (%)')
            axes[1].tick_params(axis='x', rotation=45)
            axes[1].grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.savefig(f'author_analysis_{language.lower()}.png', dpi=300, bbox_inches='tight')
        plt.show()


def visualize_language_comparison(language_comparison_df):
    """Create visualizations comparing languages"""

    char_cols = [col for col in language_comparison_df.columns if col.startswith('char_')]

    if not char_cols:
        print("No character data found for language comparison")
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Language Comparison Analysis', fontsize=16)

    # 1. Heatmap comparing languages
    char_means = language_comparison_df[char_cols].mean(skipna=False).sort_values(ascending=False)[:15]
    top_chars = char_means.index

    heatmap_data = language_comparison_df.set_index('Language')[top_chars]
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='viridis', ax=axes[0],
                cbar_kws={'shrink': 0.8})
    axes[0].set_title('Top 15 Characters by Language (%)')
    axes[0].set_xlabel('Characters')

    # 2. Top characters across all languages
    char_labels = [col.replace('char_', '') for col in char_means[:15].index]
    axes[1].bar(range(len(char_means[:15])), char_means[:15].values,
                color='lightcoral', alpha=0.7)
    axes[1].set_title('Top 15 Characters Across All Languages')
    axes[1].set_xlabel('Characters')
    axes[1].set_ylabel('Average Frequency (%)')
    axes[1].set_xticks(range(len(char_labels)))
    axes[1].set_xticklabels(char_labels, rotation=45)
    axes[1].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('language_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()


def create_summary_statistics(language_dfs, language_comparison_df, all_stats):
    """Create summary statistics and visualizations"""

    print("\n" + "="*50)
    print("SUMMARY STATISTICS")
    print("="*50)

    # Language summary
    print(f"\nLanguages analyzed: {len(language_comparison_df)}")
    total_authors = 0
    total_books = 0

    for lang in language_comparison_df['Language']:
        author_count = len(language_dfs[lang])
        total_authors += author_count

        # Count books for this language
        books_count = 0
        try:
            for author in os.listdir(os.path.join("Books", lang)):
                books_count += len(os.listdir(os.path.join("Books", lang, author)))
        except:
            pass

        total_books += books_count
        print(f"  {lang}: {author_count} authors, {books_count} books")

    print(f"\nTotal: {total_authors} authors, {total_books} books analyzed")

    # Most common characters across all languages
    char_cols = [col for col in language_comparison_df.columns if col.startswith('char_')]
    if char_cols:
        # Using skipna to make sure that languages with unique characters don't rise to the top simply because
        # other languages don't have those characters
        overall_means = language_comparison_df[char_cols].mean(skipna=False).sort_values(ascending=False)
        print(f"\nTop 10 characters across all languages:")
        for i, (char_col, freq) in enumerate(overall_means[:10].items(), 1):
            char = char_col.replace('char_', '')
            print(f"  {i:2d}. '{char}': {freq:.2f}%")


# Main execution
if __name__ == "__main__":
    # Analyze all books once and cache results
    all_stats, language_stats = analyse_all_books()

    # Generate statistics from cached results
    language_dfs, language_comparison_df = generate_language_statistics(all_stats, language_stats)

    # Save to CSV files
    save_statistics_to_csv(language_dfs, language_comparison_df)

    # Create visualizations
    visualize_author_comparison(language_dfs)
    visualize_language_comparison(language_comparison_df)

    # Print summary
    create_summary_statistics(language_dfs, language_comparison_df, all_stats)
