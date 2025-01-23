import asyncio
import time

"""The timeout is overall, not in each call"""

async def run_subprocess(command):
    """Runs an external program using asyncio."""
    process = await asyncio.create_subprocess_exec(
        *command,  # Command and arguments passed as a list
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        output = stdout.decode().strip()
        print(f"Output: {output}")
        return output
    else:
        print(f"Error: {stderr.decode().strip()}")
        return None


async def run_with_timeout(n, timeout):
    """Runs the function `n` times with an overall timeout of `timeout` seconds."""
    start_time = time.time()

    async def run_with_time_limit():
        for _ in range(n):
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                print("Timeout reached. Stopping execution.")
                return

            cmd = ["echo", "Hello, world!"]
            cmd = ["sleep", "3"]
            output = await run_subprocess(cmd)  # Example command
            if output == "YES":
                print("Detected 'YES' in output. Stopping execution.")
                return

    try:
        await asyncio.wait_for(run_with_time_limit(), timeout=timeout)
    except asyncio.TimeoutError:
        print("Overall timeout reached before completing all runs.")


if __name__ == "__main__":
    n = 5  # Number of times to run the function
    timeout = 10  # Overall timeout in seconds

    asyncio.run(run_with_timeout(n, timeout))
