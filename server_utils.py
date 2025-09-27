import redis
import socket

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_ctf_answer():
    """
    Common function for all server code to get the correct CTF answer.
    This function checks which port is currently being used and looks up
    the answer in Redis.
    """
    try:
        # Get the current socket's local port
        import inspect
        frame = inspect.currentframe()
        while frame:
            local_vars = frame.f_locals
            if 'server_socket' in local_vars:
                port = local_vars['server_socket'].getsockname()[1]
                break
            if 'port' in local_vars and isinstance(local_vars['port'], int):
                port = local_vars['port']
                break
            frame = frame.f_back
        else:
            # Fallback: try to get from global variables or other methods
            return None

        # Look up the CTF answer in Redis using the port
        ctf_answer = redis_client.get(str(port))
        return ctf_answer

    except Exception as e:
        print(f"Error getting CTF answer: {e}")
        return None