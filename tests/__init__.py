# Tests package initialization
import sys
import os
# Inject parent directory for tests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
