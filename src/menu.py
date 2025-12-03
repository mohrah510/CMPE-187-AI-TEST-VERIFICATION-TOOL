import sys
import os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MAX_TESTS, SCORE_THRESHOLD, AIRLINE_CSV, VISA_CSV
from main import run_testset
from utils.excel_writer import save_summary


def print_menu():
    print("\n1. Airline Policy Tests")
    print("2. Visa Guidance Tests")
    print("3. Both Test Sets")
    print("4. Settings")
    print("5. Exit")
    print()


def show_settings():
    import config
    print(f"\nMax Tests: {config.MAX_TESTS}")
    print(f"Threshold: {config.SCORE_THRESHOLD}%")
    print(f"OpenAI: {'✓' if config.OPENAI_API_KEY else '✗'}")
    print(f"DeepSeek: {'✓' if config.DEEPSEEK_API_KEY else '✗'}")
    print("\nEdit src/config.py to change")
    input("Press Enter...")


def run_tests(name, csv_path):
    print(f"\nRunning {name.replace('_', ' ').title()}...\n")
    try:
        run_testset(name, csv_path)
        print("\n✓ Done")
    except KeyboardInterrupt:
        print("\n✗ Cancelled")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    input("\nPress Enter...")


def run_both():
    print("\nRunning both test sets...\n")
    try:
        airline_results = run_testset("airline_policy", AIRLINE_CSV)
        visa_results = run_testset("visa_guidance", VISA_CSV)
        
        # Create summary file
        save_summary(airline_results, visa_results)
        print(f"Saved: output/test_summary.xlsx")
        
        print("\n✓ All tests completed")
    except KeyboardInterrupt:
        print("\n✗ Cancelled")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    input("\nPress Enter...")


def main():
    while True:
        print("\nAI Test Verification Tool")
        print_menu()
        
        try:
            choice = input("Select: ").strip()
            
            if choice == "1":
                run_tests("airline_policy", AIRLINE_CSV)
            elif choice == "2":
                run_tests("visa_guidance", VISA_CSV)
            elif choice == "3":
                run_both()
            elif choice == "4":
                show_settings()
            elif choice == "5":
                print("\nGoodbye\n")
                break
            else:
                print("Invalid choice\n")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye\n")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


if __name__ == "__main__":
    main()
