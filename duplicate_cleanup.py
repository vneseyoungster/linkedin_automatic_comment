import json
import os
from datetime import datetime
from collections import defaultdict

class DuplicateAuthorCleanup:
    def __init__(self):
        self.cleanup_results = {
            "cleanup_timestamp": datetime.now().isoformat(),
            "original_post_count": 0,
            "final_post_count": 0,
            "authors_processed": 0,
            "duplicates_removed": 0,
            "cleanup_strategy": "keep_first_occurrence",
            "removed_posts": []
        }

    def load_scan_data(self, filename):
        """
        Load the comprehensive scan data from JSON file
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"📚 Loaded scan data from {filename}")
            return data
        except Exception as e:
            print(f"❌ Error loading scan data: {e}")
            return None

    def analyze_duplicates(self, posts_data):
        """
        Analyze duplicate authors in the posts data
        """
        author_posts = defaultdict(list)

        # Group posts by author
        for post in posts_data:
            author_name = post.get("author_name")
            if author_name:
                author_posts[author_name].append(post)

        print(f"\n📊 DUPLICATE ANALYSIS:")
        print(f"Total unique authors: {len(author_posts)}")

        duplicate_authors = {}
        for author, posts in author_posts.items():
            if len(posts) > 1:
                duplicate_authors[author] = posts
                print(f"🔄 {author}: {len(posts)} posts")

        print(f"Authors with duplicates: {len(duplicate_authors)}")

        return author_posts, duplicate_authors

    def cleanup_duplicates(self, posts_data, strategy="keep_first_normal"):
        """
        Remove duplicate posts from the same author

        Strategies:
        - keep_first_normal: Keep first normal post, remove sponsored duplicates
        - keep_first_occurrence: Keep the first post found (regardless of type)
        - keep_normal_only: Keep only normal posts, remove all sponsored
        - keep_latest_ember: Keep post with highest ember ID number
        """
        self.cleanup_results["cleanup_strategy"] = strategy
        self.cleanup_results["original_post_count"] = len(posts_data)

        author_posts = defaultdict(list)

        # Group posts by author
        for post in posts_data:
            author_name = post.get("author_name")
            if author_name:
                author_posts[author_name].append(post)

        self.cleanup_results["authors_processed"] = len(author_posts)

        cleaned_posts = []

        for author, posts in author_posts.items():
            if len(posts) == 1:
                # No duplicates, keep the post
                cleaned_posts.append(posts[0])
            else:
                # Multiple posts from same author - apply strategy
                kept_post = self._apply_cleanup_strategy(posts, strategy)
                if kept_post:
                    cleaned_posts.append(kept_post)

                    # Record removed posts
                    for post in posts:
                        if post != kept_post:
                            self.cleanup_results["removed_posts"].append({
                                "ember_id": post.get("ember_id"),
                                "author_name": post.get("author_name"),
                                "is_sponsored": post.get("is_sponsored"),
                                "reason": f"duplicate_author_{strategy}"
                            })
                            self.cleanup_results["duplicates_removed"] += 1

        self.cleanup_results["final_post_count"] = len(cleaned_posts)

        print(f"\n✨ CLEANUP COMPLETED:")
        print(f"Original posts: {self.cleanup_results['original_post_count']}")
        print(f"Final posts: {self.cleanup_results['final_post_count']}")
        print(f"Duplicates removed: {self.cleanup_results['duplicates_removed']}")

        return cleaned_posts

    def _apply_cleanup_strategy(self, posts, strategy):
        """
        Apply the specified cleanup strategy to select which post to keep
        """
        if strategy == "keep_first_normal":
            # Prefer normal posts over sponsored
            normal_posts = [p for p in posts if not p.get("is_sponsored", False)]
            if normal_posts:
                return normal_posts[0]  # First normal post
            else:
                return posts[0]  # If all sponsored, keep first

        elif strategy == "keep_first_occurrence":
            # Keep the first post found
            return posts[0]

        elif strategy == "keep_normal_only":
            # Only keep normal posts, skip all sponsored
            normal_posts = [p for p in posts if not p.get("is_sponsored", False)]
            return normal_posts[0] if normal_posts else None

        elif strategy == "keep_latest_ember":
            # Keep post with highest ember ID number
            def get_ember_number(post):
                ember_id = post.get("ember_id", "ember0")
                try:
                    return int(ember_id.replace("ember", ""))
                except:
                    return 0

            return max(posts, key=get_ember_number)

        else:
            # Default: keep first occurrence
            return posts[0]

    def clean_scan_file(self, input_filename, output_filename=None, strategy="keep_first_normal"):
        """
        Main function to clean up a scan file and save the cleaned version
        """
        print(f"🧹 Starting duplicate cleanup for {input_filename}")
        print(f"Strategy: {strategy}")
        print("=" * 60)

        # Load original data
        scan_data = self.load_scan_data(input_filename)
        if not scan_data:
            return False

        # Analyze duplicates first
        print("\n🔍 Analyzing duplicate authors...")
        author_posts, duplicate_authors = self.analyze_duplicates(scan_data.get("posts_data", []))

        if not duplicate_authors:
            print("✅ No duplicate authors found - no cleanup needed!")
            return True

        # Clean up posts_data
        print(f"\n🧹 Applying cleanup strategy: {strategy}")
        cleaned_posts_data = self.cleanup_duplicates(scan_data.get("posts_data", []), strategy)

        # Rebuild normal_posts and sponsored_posts arrays
        normal_posts = [p for p in cleaned_posts_data if not p.get("is_sponsored", False)]
        sponsored_posts = [p for p in cleaned_posts_data if p.get("is_sponsored", False)]

        # Update the scan data
        cleaned_scan_data = scan_data.copy()
        cleaned_scan_data["posts_data"] = cleaned_posts_data
        cleaned_scan_data["normal_posts"] = normal_posts
        cleaned_scan_data["sponsored_posts"] = sponsored_posts

        # Update scan summary
        cleaned_scan_data["scan_summary"] = {
            "total_ember_elements": scan_data["scan_summary"].get("total_ember_elements", 0),
            "total_posts_processed": len(cleaned_posts_data),
            "total_posts_with_authors": len(cleaned_posts_data),
            "normal_posts_count": len(normal_posts),
            "sponsored_posts_count": len(sponsored_posts),
            "unique_authors_count": len(set([p["author_name"] for p in cleaned_posts_data if p["author_name"]]))
        }

        # Add cleanup metadata
        cleaned_scan_data["cleanup_info"] = self.cleanup_results
        cleaned_scan_data["cleanup_applied"] = True
        cleaned_scan_data["original_scan_timestamp"] = scan_data.get("scan_timestamp")
        cleaned_scan_data["scan_timestamp"] = datetime.now().isoformat()

        # Save cleaned data
        if output_filename is None:
            # Create backup of original and overwrite
            backup_filename = input_filename.replace(".json", "_backup.json")
            try:
                os.rename(input_filename, backup_filename)
                print(f"📦 Original file backed up as: {backup_filename}")
            except Exception as e:
                print(f"⚠️ Could not create backup: {e}")

            output_filename = input_filename

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_scan_data, f, indent=2, ensure_ascii=False)

            print(f"💾 Cleaned data saved to: {output_filename}")

            # Print final summary
            self.print_cleanup_summary(cleaned_scan_data)

            return True

        except Exception as e:
            print(f"❌ Error saving cleaned data: {e}")
            return False

    def print_cleanup_summary(self, cleaned_data):
        """
        Print a detailed summary of the cleanup process
        """
        print(f"\n{'='*60}")
        print("📊 DUPLICATE CLEANUP SUMMARY")
        print(f"{'='*60}")

        cleanup_info = cleaned_data.get("cleanup_info", {})
        summary = cleaned_data.get("scan_summary", {})

        print(f"🧹 Cleanup Strategy: {cleanup_info.get('cleanup_strategy')}")
        print(f"📝 Original Posts: {cleanup_info.get('original_post_count', 0)}")
        print(f"✨ Final Posts: {cleanup_info.get('final_post_count', 0)}")
        print(f"🗑️ Duplicates Removed: {cleanup_info.get('duplicates_removed', 0)}")
        print(f"👥 Authors Processed: {cleanup_info.get('authors_processed', 0)}")
        print(f"👤 Unique Authors: {summary.get('unique_authors_count', 0)}")

        print(f"\n📊 Final Distribution:")
        print(f"📄 Normal Posts: {summary.get('normal_posts_count', 0)}")
        print(f"📢 Sponsored Posts: {summary.get('sponsored_posts_count', 0)}")

        # Show removed posts sample
        removed_posts = cleanup_info.get("removed_posts", [])
        if removed_posts:
            print(f"\n🗑️ Sample Removed Posts:")
            print("-" * 40)
            for i, removed in enumerate(removed_posts[:5], 1):
                sponsor_tag = " [SPONSORED]" if removed.get("is_sponsored") else ""
                print(f"{i}. {removed.get('author_name')}{sponsor_tag} ({removed.get('ember_id')})")

            if len(removed_posts) > 5:
                print(f"... and {len(removed_posts) - 5} more")

        print(f"{'='*60}")

    def quick_cleanup(self, filename="linkedin_comprehensive_scan.json", strategy="keep_first_normal"):
        """
        Quick cleanup function for easy usage
        """
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return False

        return self.clean_scan_file(filename, strategy=strategy)


def main():
    """
    Standalone function for testing duplicate cleanup
    """
    print("🧹 LinkedIn Duplicate Author Cleanup Tool")
    print("=" * 50)

    cleaner = DuplicateAuthorCleanup()

    # Check for scan file
    scan_file = "linkedin_comprehensive_scan.json"
    if not os.path.exists(scan_file):
        print(f"❌ Scan file not found: {scan_file}")
        print("Run test.py first to generate the scan data.")
        return

    # Show available strategies
    strategies = {
        "1": ("keep_first_normal", "Keep first normal post, remove sponsored duplicates"),
        "2": ("keep_first_occurrence", "Keep the first post found (regardless of type)"),
        "3": ("keep_normal_only", "Keep only normal posts, remove all sponsored"),
        "4": ("keep_latest_ember", "Keep post with highest ember ID number")
    }

    print("\nAvailable cleanup strategies:")
    for key, (strategy, description) in strategies.items():
        print(f"{key}. {description}")

    choice = input("\nSelect strategy (1-4, or Enter for default): ").strip()

    if choice in strategies:
        strategy_name = strategies[choice][0]
    else:
        strategy_name = "keep_first_normal"  # Default

    print(f"\nUsing strategy: {strategy_name}")

    # Perform cleanup
    success = cleaner.quick_cleanup(scan_file, strategy_name)

    if success:
        print("\n✅ Cleanup completed successfully!")
        print(f"💾 Cleaned data saved to: {scan_file}")
        print(f"📦 Original backed up with _backup.json suffix")
    else:
        print("\n❌ Cleanup failed!")

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()