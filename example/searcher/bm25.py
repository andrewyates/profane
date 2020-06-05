from profane import ModuleBase, Dependency, ConfigOption


class Searcher(ModuleBase):
    module_type = "searcher"


@Searcher.register
class BM25(Searcher):
    module_name = "BM25"
    dependencies = [Dependency(key="index", module="index", name="anserini")]
    config_spec = [ConfigOption(key="b", default_value="0.8", description="b param")]
    requires_random_seed = True
