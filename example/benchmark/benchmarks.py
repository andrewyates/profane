from profane import ModuleBase, Dependency, ConfigOption


class Benchmark(ModuleBase):
    module_type = "benchmark"


@Benchmark.register
class WsdmBenchmark(Benchmark):
    module_name = "wsdm20demo"

    dependencies = [Dependency(key="collection", module="collection", name="robust04")]
