import pytest

# import constants
from profane.base import (
    ModuleBase,
    PipelineConstructionError,
    ConfigOption,
    InvalidConfigError,
    Dependency,
    module_registry,
    constants,
    _DEFAULT_RANDOM_SEED,
)


@pytest.fixture
def rank_modules():
    module_registry.reset()
    constants.reset()

    class Task(ModuleBase):
        module_type = "task"
        requires_random_seed = True

    @Task.register
    class ThreeRankTask(Task):
        """A strange rank task that runs two searchers on benchmark #1 (via TwoRank) and the third searcher on benchmark #2"""

        module_name = "threerank"
        dependencies = [
            Dependency(key="tworank", module="task", name="tworank"),
            Dependency(key="rank3", module="task", name="rank"),
        ]

    @Task.register
    class TwoRankTask(Task):
        """A rank tasks two runs two searchers on the same benchmark"""

        module_name = "tworank"
        dependencies = [
            Dependency(key="benchmark", module="benchmark", name="rob04yang", provide_this=True, provide_children=["collection"]),
            Dependency(key="rank1a", module="task", name="rank"),
            Dependency(key="rank1b", module="task", name="rank"),
        ]

    @Task.register
    class RankTask(Task):
        module_name = "rank"
        dependencies = [
            Dependency(key="benchmark", module="benchmark", name="rob04yang", provide_this=True, provide_children=["collection"]),
            Dependency(key="searcher", module="searcher", name="bm25"),
        ]

    @Task.register
    class RerankTask(Task):
        module_name = "rerank"
        config_spec = [
            ConfigOption("fold", "s1", "fold to run"),
            ConfigOption(
                "optimize", "map", "metric to maximize on the dev set"
            ),  # affects train() because we check to save weights
        ]
        dependencies = [
            Dependency(key="benchmark", module="benchmark", name="rob04yang", provide_this=True, provide_children=["collection"]),
            Dependency(key="rank", module="task", name="rank"),
            Dependency(key="reranker", module="reranker", name="DRMM"),
        ]

    @ModuleBase.register
    class BenchmarkRob04(ModuleBase):
        module_type = "benchmark"
        module_name = "rob04yang"
        dependencies = [Dependency(key="collection", module="collection", name="robust04")]

    @ModuleBase.register
    class BenchmarkTRECDL(ModuleBase):
        module_type = "benchmark"
        module_name = "trecdl"
        dependencies = [Dependency(key="collection", module="collection", name="msmarco")]

    @ModuleBase.register
    class SearcherBM25(ModuleBase):
        module_type = "searcher"
        module_name = "bm25"
        dependencies = [Dependency(key="index", module="index", name="anserini")]
        config_spec = [ConfigOption(key="k1", default_value=1.0, description="k1 parameter")]
        # Searchers are unlikely to actually need a seed, but we require it for testing
        requires_random_seed = True

    @ModuleBase.register
    class IndexAnserini(ModuleBase):
        module_type = "index"
        module_name = "anserini"
        dependencies = [Dependency(key="collection", module="collection", name="robust04")]
        config_spec = [ConfigOption(key="stemmer", default_value="porter", description="stemming")]

    @ModuleBase.register
    class CollectionRobust04(ModuleBase):
        module_type = "collection"
        module_name = "robust04"

    @ModuleBase.register
    class CollectionMSMARCO(ModuleBase):
        module_type = "collection"
        module_name = "msmarco"

    @ModuleBase.register
    class ExtractorEmbedtext(ModuleBase):
        module_type = "extractor"
        module_name = "embedtext"

        dependencies = [
            Dependency(key="index", module="index", name="anserini", default_config_overrides={"stemmer": "none"}),
            Dependency(key="tokenizer", module="tokenizer", name="anserini"),
        ]
        config_spec = [
            ConfigOption("embeddings", "glove6b"),
            ConfigOption("zerounk", False),
            ConfigOption("calcidf", True),
            ConfigOption("maxqlen", 4),
            ConfigOption("maxdoclen", 800),
            ConfigOption("usecache", False),
        ]

    @ModuleBase.register
    class TokenizerAnserini(ModuleBase):
        module_type = "tokenizer"
        module_name = "anserini"
        config_spec = [
            ConfigOption("keepstops", True, "keep stopwords if True"),
            ConfigOption("stemmer", "none", "stemmer: porter, krovetz, or none"),
        ]

    @ModuleBase.register
    class TrainerPytorch(ModuleBase):
        module_type = "trainer"
        module_name = "pytorch"
        config_spec = [
            ConfigOption("batch", 32, "batch size"),
            ConfigOption("niters", 20),
            ConfigOption("itersize", 512),
            ConfigOption("gradacc", 1),
            ConfigOption("lr", 0.001),
            ConfigOption("softmaxloss", False),
            ConfigOption("fastforward", False),
            ConfigOption("validatefreq", 1),
            ConfigOption("boardname", "default"),
        ]
        config_keys_not_in_path = ["fastforward", "boardname"]

    @ModuleBase.register
    class RerankerDRMM(ModuleBase):
        module_type = "reranker"
        module_name = "DRMM"
        dependencies = [
            Dependency(key="extractor", module="extractor", name="embedtext"),
            Dependency(key="trainer", module="trainer", name="pytorch"),
        ]
        config_spec = [
            ConfigOption("nbins", 29, "number of bins in matching histogram"),
            ConfigOption("nodes", 5, "hidden layer dimension for matching network"),
            ConfigOption("histType", "LCH", "histogram type: CH, NH, LCH"),
            ConfigOption("gateType", "IDF", "term gate type: TV or IDF"),
        ]

    return [ThreeRankTask, TwoRankTask, RankTask, RerankTask]


def test_creation_with_simple_provide(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    # non-default collection should be set in both benchmark's and searcher's dependencies
    rank = RankTask({"benchmark": {"collection": {"name": "msmarco"}}})
    assert rank.benchmark.collection.module_name == "msmarco"
    assert rank.searcher.index.collection.module_name == "msmarco"
    assert rank.benchmark.collection == rank.searcher.index.collection


def test_creation_with_complex_provide(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    # TwoRank task should provide same default benchmark to both Rank tasks
    tworank_default = TwoRankTask()
    assert tworank_default.rank1a.benchmark == tworank_default.rank1b.benchmark
    assert tworank_default.rank1a.benchmark.module_name == "rob04yang"
    # and should provide same default collection to rank.searcher.index
    assert tworank_default.rank1a.searcher.index.collection == tworank_default.rank1b.searcher.index.collection
    assert tworank_default.rank1a.searcher.index.collection.module_name == "robust04"
    # re-using the config should yield a new object with the same config
    assert tworank_default.config == TwoRankTask(tworank_default.config).config

    # TwoRank task should provide same non-default benchmark to both Rank tasks
    tworank_trecdl = TwoRankTask({"benchmark": {"name": "trecdl"}})
    assert tworank_trecdl.rank1a.benchmark == tworank_trecdl.rank1b.benchmark
    assert tworank_trecdl.rank1a.benchmark.module_name == "trecdl"
    # and should provide same non-default collection to rank.searcher.index
    assert tworank_trecdl.rank1a.searcher.index.collection == tworank_trecdl.rank1b.searcher.index.collection
    assert tworank_trecdl.rank1a.searcher.index.collection.module_name == "msmarco"
    # re-using the config should yield a new object with the same config
    assert tworank_trecdl.config == TwoRankTask(tworank_trecdl.config).config


def test_creation_with_more_complex_provide(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    # this ThreeRank should provide a TwoRank with one benchmark and a Rank with a second (independent) benchmark
    threerank = ThreeRankTask({"tworank": {"benchmark": {"name": "rob04yang"}}, "rank3": {"benchmark": {"name": "trecdl"}}})
    assert threerank.tworank.rank1a.benchmark == threerank.tworank.rank1b.benchmark
    assert threerank.tworank.rank1a.searcher.index.collection == threerank.tworank.rank1b.searcher.index.collection
    assert threerank.tworank.benchmark.module_name == "rob04yang"
    assert threerank.rank3.benchmark.module_name == "trecdl"
    assert threerank.tworank.rank1a.searcher.index.collection.module_name == "robust04"
    assert threerank.rank3.searcher.index.collection.module_name == "msmarco"
    # re-using the config should yield a new object with the same config
    assert threerank.config == ThreeRankTask(threerank.config).config


def test_creation_with_module_object_sharing(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    tworank_trecdl = TwoRankTask({"benchmark": {"name": "trecdl"}}, share_objects=True)
    # both Rank tasks should be identical and thus pointing to the same object
    assert tworank_trecdl.rank1a == tworank_trecdl.rank1b
    # however, the TwoRankTask object is not shared because .create() was not used
    assert tworank_trecdl != TwoRankTask(tworank_trecdl.config)

    # calling .create() twice returns the same object when the config is the same
    assert TwoRankTask.create("tworank", tworank_trecdl.config) == TwoRankTask.create("tworank", tworank_trecdl.config)
    # and different objects when the configs are different
    assert TwoRankTask.create("tworank", tworank_trecdl.config) != TwoRankTask.create("tworank")

    # change k1 so that Rank and Searcher objects should be different
    tworank_k1 = TwoRankTask({"rank1a": {"searcher": {"k1": 0.5}}, "rank1b": {"searcher": {"k1": 1.0}}}, share_objects=True)
    assert tworank_k1.rank1a.benchmark == tworank_k1.rank1b.benchmark
    assert tworank_k1.rank1a.searcher.index == tworank_k1.rank1b.searcher.index
    # but Benchmark and Index should be the same objects
    assert tworank_k1.rank1a != tworank_k1.rank1b
    assert tworank_k1.rank1a.searcher != tworank_k1.rank1b.searcher
    # and rank1b should be the same object as used in tworank_default
    tworank_default = TwoRankTask(share_objects=True)
    assert tworank_k1.rank1b == tworank_default.rank1b

    # this ThreeRank should use the same benchmark for both its TwoRank and Rank
    threerank_same = ThreeRankTask(
        {"tworank": {"benchmark": {"name": "trecdl"}}, "rank3": {"benchmark": {"name": "trecdl"}}}, share_objects=True
    )
    assert threerank_same.tworank.benchmark == threerank_same.rank3.benchmark


def test_module_path(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    rt = RankTask({"searcher": {"index": {"stemmer": "other"}}})
    assert (
        rt.get_module_path()
        == "collection-robust04/benchmark-rob04yang/collection-robust04/index-anserini_stemmer-other/searcher-bm25_k1-1.0_seed-42/task-rank_seed-42"
    )
    assert rt.benchmark.get_module_path() == "collection-robust04/benchmark-rob04yang"
    assert rt.searcher.get_module_path() == "collection-robust04/index-anserini_stemmer-other/searcher-bm25_k1-1.0_seed-42"

    rrt = RerankTask()
    assert (
        rrt.get_module_path()
        == "collection-robust04/benchmark-rob04yang/collection-robust04/benchmark-rob04yang/collection-robust04/index-anserini_stemmer-porter/searcher-bm25_k1-1.0_seed-42/task-rank_seed-42/collection-robust04/index-anserini_stemmer-None/tokenizer-anserini_keepstops-True_stemmer-None/extractor-embedtext_calcidf-True_embeddings-glove6b_maxdoclen-800_maxqlen-4_usecache-False_zerounk-False/trainer-pytorch_batch-32_gradacc-1_itersize-512_lr-0.001_niters-20_softmaxloss-False_validatefreq-1/reranker-DRMM_gateType-IDF_histType-LCH_nbins-29_nodes-5/task-rerank_fold-s1_optimize-map_seed-42"
    )
    assert rrt.benchmark.get_module_path() == "collection-robust04/benchmark-rob04yang"
    assert (
        rrt.rank.get_module_path()
        == "collection-robust04/benchmark-rob04yang/collection-robust04/index-anserini_stemmer-porter/searcher-bm25_k1-1.0_seed-42/task-rank_seed-42"
    )


def test_config_keys_not_in_module_path():
    @ModuleBase.register
    class CollectionSecret(ModuleBase):
        module_type = "collection"
        module_name = "secretdocs"
        config_keys_not_in_path = ["path"]
        config_spec = [
            ConfigOption(key="version", default_value="aliens", description="redacted"),
            ConfigOption(key="path", default_value="nicetry", description="redacted"),
        ]

    collection = CollectionSecret({"version": "illuminati"})
    assert collection.get_module_path() == "collection-secretdocs_version-illuminati"


def test_config_seed_propagation(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    rt = RankTask({"seed": 123, "searcher": {"index": {"stemmer": "other"}}})
    assert rt.config["seed"] == 123
    assert rt.searcher.config["seed"] == 123


def test_config_seed_nonpropagation(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    rt = RankTask({"searcher": {"seed": 123, "index": {"stemmer": "other"}}})
    assert rt.config["seed"] == _DEFAULT_RANDOM_SEED
    assert rt.searcher.config["seed"] == _DEFAULT_RANDOM_SEED


def test_prng_creation(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    rt = RankTask({"searcher": {"seed": 123, "index": {"stemmer": "other"}}})
    assert hasattr(rt, "rng")
    assert hasattr(rt.searcher, "rng")

    assert not hasattr(rt.searcher.index, "rng")
    assert not hasattr(rt.searcher.index.collection, "rng")
    assert not hasattr(rt.benchmark, "rng")
    assert not hasattr(rt.benchmark.collection, "rng")


def test_creation_with_config_string(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    rt1 = RankTask({"searcher": {"seed": 123, "index": {"stemmer": "other"}}})
    rt2 = RankTask("searcher.seed=123 searcher.index.stemmer=other")
    rt3 = RankTask("searcher.seed=456 searcher.seed=123 searcher.index.stemmer=other")

    assert rt1.config == rt2.config
    assert rt2.config == rt3.config


def test_creation_with_provide_obj(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    benchmark = module_registry.lookup("benchmark", "trecdl")()
    rt = RankTask("benchmark.name=rob04yang", provide=benchmark)

    assert rt.benchmark == benchmark


def test_creation_with_provide_list(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    benchmark = module_registry.lookup("benchmark", "trecdl")()
    rt = RankTask("benchmark.name=rob04yang", provide=[benchmark])

    assert rt.benchmark == benchmark


def test_skip_config_in_module_path(rank_modules):
    ThreeRankTask, TwoRankTask, RankTask, RerankTask = rank_modules

    rerank = RerankTask()
    assert rerank.get_module_path().endswith("/task-rerank_fold-s1_optimize-map_seed-42")
    assert rerank.get_module_path(skip_config_keys="fold").endswith("/task-rerank_optimize-map_seed-42")
    assert rerank.get_module_path(skip_config_keys=["fold", "seed"]).endswith("/task-rerank_optimize-map")


def test_registry_enumeration(rank_modules):
    assert module_registry.get_module_types() == [
        "benchmark",
        "collection",
        "extractor",
        "index",
        "reranker",
        "searcher",
        "task",
        "tokenizer",
        "trainer",
    ]
    assert module_registry.get_module_names("benchmark") == ["rob04yang", "trecdl"]
    assert module_registry.get_module_names("collection") == ["msmarco", "robust04"]
    assert module_registry.get_module_names("index") == ["anserini"]
    assert module_registry.get_module_names("searcher") == ["bm25"]
    assert module_registry.get_module_names("task") == ["rank", "rerank", "threerank", "tworank"]
