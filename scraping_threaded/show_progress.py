# ===========================================================================
#                            Scraping Progress
# ===========================================================================

from tabulate import tabulate
from datetime import datetime
from utils.database import *
import click
import time

# ================================= HELPERS ================================


def calcDiff(previous_counts, new_counts):
    result = []
    for item2 in new_counts:

        # New count
        id_value2 = item2.get('_id', "")
        count2 = item2.get('count', 0)

        for item1 in previous_counts:

            # Prev count
            id_value1 = item1.get('_id', "")
            count1 = item1.get('count', 0)

            if id_value1 == id_value2:
                diff = count2 - count1
                break
        else:
            diff = count2
            count1 = 0

        result.append({'_id': id_value2, 'previous_count': count1,
                       'new_count': count2, 'diff': diff})

    return result


def calcRate(results, timer):
    elapsed = (time.time() - timer) if timer else None
    timer = time.time()
    for status in results:
        if elapsed:
            rate = round(status.get("diff", 0) / elapsed)
            color = "green" if rate >= 0 else "red"
            status["rate"] = click.style(str(rate), fg=color)
        else:
            status["previous_count"] = click.style(str("-"), fg="bright_black")
            status["rate"] = click.style(str("-"), fg="bright_black")
            status["diff"] = click.style(str("-"), fg="bright_black")
    return timer, results

# ================================= MAIN ================================

# fmt: off
@click.command()
@click.option("--refresh_rate", default=5, help="Refresh every n seconds")
# fmt: on
def main(refresh_rate):

    # Connect to database
    _, db = getConnection(use_dotenv=True)

    click.echo(click.style("Loading results ...", fg="blue", bold=True))
    results = {}
    timer = None

    while True:

        # Fetch data and calculate diff
        new_results = countProcessingStatus(db)
        results_diff = calcDiff(results, new_results)
        timer, results_diff = calcRate(results_diff, timer)
        results = new_results
        click.clear()

        # Header
        click.echo(click.style("Processing Status:", fg="blue", bold=True))

        # Content: current status and document counts
        header_names = {"_id": "Status", "previous_count": "Prev. Count",
                        "new_count": "Count", "diff": "Diff", "rate": "Rate"}
        print(tabulate(results_diff, headers=header_names))

        # Footer
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        click.echo(click.style(f"Last updated: {current_time}", fg="green"))
        click.echo(click.style(f"Press Ctrl + c to exit", fg="green"))

        # Wait before refresh
        time.sleep(float(refresh_rate))


if __name__ == "__main__":
    main()
