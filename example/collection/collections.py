from profane import ModuleBase, Dependency, ConfigOption


class Collection(ModuleBase):
    module_type = "collection"


@Collection.register
class Robust04(Collection):
    module_name = "robust04"


@Collection.register
class MSMARCO(Collection):
    module_name = "MSMARCO"
