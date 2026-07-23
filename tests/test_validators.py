import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from intellidue_core.validators import validate_state, validate_release_lock, validate_zip

class TestValidators(unittest.TestCase):
    def setUp(self): self.fx=ROOT/'tests/fixtures/synthetic_project'
    def test_state(self): self.assertEqual(validate_state(self.fx/'current_project_state.json'),[])
    def test_lock(self): self.assertEqual(validate_release_lock(self.fx/'release_lock.json'),[])
    def test_zip(self): self.assertEqual(validate_zip(self.fx/'package.zip'),[])

if __name__=='__main__': unittest.main()
