import asyncio
import time

"""The timeout is on each process call"""

async def run_subprocess(command, time_left):
    """Runs an external program using asyncio."""
    process = await asyncio.create_subprocess_exec(
        *command,  # Command and arguments passed as a list
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=time_left)

    if process.returncode == 0:
        output = stdout.decode().strip()
        print(f"Output: {output}")
        return output
    else:
        print(f"Error: {stderr.decode().strip()}")
        return None


async def run_with_timeout(n, timeout):
    """Runs the function `n` times with an overall timeout of `timeout` seconds."""

    async def run_with_time_limit():
        time_left = timeout
        for _ in range(n):
            start_time = time.time()
            # if elapsed >= timeout:
            #     print("Timeout reached. Stopping execution.")
            #     return

            cmd = ["echo", "Hello, world!"]
            cmd = ["sleep", "3"]
            print(time_left)
            output = await run_subprocess(cmd, time_left)  # Example command
            if output == "YES":
                print("Detected 'YES' in output. Stopping execution.")
                return
            time_left -= time.time() - start_time

    try:
        await run_with_time_limit()
        print("done!")
    except asyncio.TimeoutError as e:
        print("Overall timeout reached before completing all runs.", e)


if __name__ == "__main__":
    n = 5  # Number of times to run the function
    timeout = 10  # Overall timeout in seconds

    asyncio.run(run_with_timeout(n, timeout))
