# ===========================================================================
#                            Extract Article Content
# ===========================================================================
# Use this script fo scrape the content of the articles

from utils.database import *
from time import perf_counter
from threading import Thread
import logging
import click
import sys

from parser.default import DefaultParser

# ---------------------------------------------------------------------------
#                            HELPERS
# ---------------------------------------------------------------------------


def chunks(l, n):
    """Yield n number of striped chunks from l."""
    for i in range(0, n):
        yield l[i::n]


def toLarge(variable, limit=15.5):
    """Check if variable is to large"""
    size_in_bytes = sys.getsizeof(variable)
    size_in_MB = size_in_bytes / (1024 * 1024)  # Convert bytes to megabytes
    return size_in_MB > limit

# ---------------------------------------------------------------------------
#                            MULTIPROCESSING
# ---------------------------------------------------------------------------


def processTasks(id, tasks, logger, db, fs):
    logger.info(f"Worker {id} started ...")

    # Initiate parser
    parser = DefaultParser()

    for task_id, task in enumerate(tasks):

        try:

            url = task["url"]
            file_id = task.get("scraping_result", {}).get("content_html", None)

            if not file_id or file_id == "None":
                logger.info(
                    f"Worker {id:2}: [{task_id}/{len(tasks)}] No html content found for {url}")
            else:
                response = getPageContent(fs, file_id, encoding="UTF-8")

                # Parse the article content from the response object
                text, error = parser.extractText(url, response)

                # Write webpage content to file system
                # meta = {"target_url": task["url"], "article_id": task["_id"]}
                # file_id = savePageContent(
                #    fs, text, encoding="UTF-8", attr=meta)

                if not toLarge(text):
                    # Updated tasks by changig status and info about sraping results
                    values = {"text_extracted": True,
                              "status": "CONTENT-EXTRACTED",
                              "parsing_result": {
                                  "text": text,
                                  "text_length": len(text),
                                  "word_count": len(text.split(" ")),
                                  "parsing_error": error}
                              }

                    # result = {"content_txt": str(file_id)}
                    updateTask(db, task["_id"], values, None)

                    logger.info(
                        f"Worker {id:2}: [{task_id}/{len(tasks)}] Characters extracted: {len(text):4} - {text.strip()[:50]:50}")
                else:
                    logger.error(
                        f"Worker {id:2}: [{task_id}/{len(tasks)}] Text to large for {url}")

        except Exception as e:
            logger.error(f"Worker {id:2}:  {repr(e)}")

    logger.info(f"Worker {id:2}: finished")


# ---------------------------------------------------------------------------
#                            MAIN
# ---------------------------------------------------------------------------

# fmt: off
@click.command()
@click.option("--path_logfile", default="logs_extraction.log", help="Logfile location") 
@click.option("--workers", default=8, help="Number of threads used for scraping")
@click.option("--limit", default=512_00, help="Only scraping first n urls (0 equals no limit)")
@click.option('--status', default="CONTENT-FETCHED", help="Any status")
@click.option("--batch", default="last", help="all, first last, or a number indicating the batch")
def main(path_logfile, workers, 
       limit, status,  batch): 

    # ------------------- LOGGING -------------------

    # Create logger
    logger = logging.getLogger("main")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s  %(levelname)-8s %(message)s")

    # Log to terminal
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # Log to file
    file_handler = logging.FileHandler(path_logfile)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("Extraction Scraping Run")

    # fmt: on
    timer_start = perf_counter()

    # ------------------- DATABASE -------------------

    # Connect to Database
    fs, db = getConnection(use_dotenv=True)
    # only retrieve the fields that are necessary for the scraping
    fields = {'scraping_result': 1, 'url': 1}

    # ------------------- FETCH TASKS -------------------

    tasks = fetchTasks(db, None, status, limit, fields)
    logger.info(f"Number of URLs: {len(tasks)}")

    # ------------------- FETCH CONTENT -------------------

    logger.info(f"Number of URLs to be scraped: {len(tasks)}")

    # if there is more than worker use threads
    if workers > 1:

        threads = []

        # Create one thread per chunk
        for id, chunk in enumerate(chunks(tasks, workers)):

            # Package arguments
            args = (id, chunk, logger, db, fs)  # fmt: skip

            # Create and start thread
            t = Thread(target=processTasks, args=args)
            threads.append(t)
            t.start()

        # Wait for the threads to complete
        for t in threads:
            t.join()

    else:
        processTasks(-1, tasks, logger, db, fs)

    # ------------------- WRAP UP -------------------

    # Print runtime
    timer_stop = perf_counter()
    logger.info("Ending Scraping Run")
    logger.info("Runtime: " + str(round(timer_stop - timer_start, 4)))


if __name__ == "__main__":
    main()
