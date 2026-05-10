import sys, os, importlib.util, importlib.machinery
class FlatImporter:
    def find_spec(self, fullname, path, target=None):
        parts = fullname.split('.')
        if parts[0] in ['app', 'api', 'src', 'core', 'models', 'routers', 'endpoints', 'services', 'utils', 'db', 'schemas', 'controllers', 'config']:
            name = parts[-1]
            if os.path.exists(name + '.py'):
                return importlib.util.spec_from_file_location(fullname, os.path.abspath(name + '.py'))
            class DummyLoader:
                def create_module(self, spec): return None
                def exec_module(self, module): pass
            return importlib.machinery.ModuleSpec(fullname, DummyLoader(), is_package=True)
        return None
sys.meta_path.append(FlatImporter())