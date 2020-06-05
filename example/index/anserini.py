from profane import ModuleBase, Dependency, ConfigOption


class Index(ModuleBase):
    module_type = "index"


@Index.register
class Anserini(Index):
    module_name = "anserini"
    dependencies = [Dependency(key="collection", module="collection", name="MSMARCO")]
    config_spec = [ConfigOption(key="stemmer", default_value="porter", description="stemmer")]
