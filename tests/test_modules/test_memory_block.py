__doc__ = """" Test modules to construct memory block """

import pytest
import numpy as np

from elastica.rod import RodBase
from elastica.modules.memory_block import construct_memory_block_structures
from elastica.memory_block.memory_block_rod import MemoryBlockCosseratRod


class BaseRodForTesting(RodBase):
    def __init__(self, n_elems):
        self.n_elems = n_elems  # np.random.randint(10, 30 + 1)
        self.n_nodes = self.n_elems + 1
        self.n_voronoi = self.n_elems - 1
        self.ring_rod_flag = False

        # Things that are scalar mapped on nodes
        self.mass = np.random.randn(self.n_nodes)

        # Things that are vectors mapped on nodes
        self.position_collection = np.random.randn(3, self.n_nodes)
        self.velocity_collection = np.random.randn(3, self.n_nodes)
        self.acceleration_collection = np.random.randn(3, self.n_nodes)
        self.internal_forces = np.random.randn(3, self.n_nodes)
        self.external_forces = np.random.randn(3, self.n_nodes)

        # Things that are scalar mapped on elements
        self.radius = np.random.rand(self.n_elems)
        self.volume = np.random.rand(self.n_elems)
        self.density = np.random.rand(self.n_elems)
        self.lengths = np.random.rand(self.n_elems)
        self.rest_lengths = self.lengths.copy()
        self.dilatation = np.random.rand(self.n_elems)
        self.dilatation_rate = np.random.rand(self.n_elems)

        # Things that are vector mapped on elements
        self.omega_collection = np.random.randn(3, self.n_elems)
        self.alpha_collection = np.random.randn(3, self.n_elems)
        self.tangents = np.random.randn(3, self.n_elems)
        self.sigma = np.random.randn(3, self.n_elems)
        self.rest_sigma = np.random.randn(3, self.n_elems)
        self.internal_torques = np.random.randn(3, self.n_elems)
        self.external_torques = np.random.randn(3, self.n_elems)
        self.internal_stress = np.random.randn(3, self.n_elems)

        # Things that are matrix mapped on elements
        self.director_collection = np.tile(
            np.eye(3).reshape(3, 3, 1), (1, 1, self.n_elems)
        )
        self.mass_second_moment_of_inertia = np.random.randn() * np.ones(
            (3, 3, self.n_elems)
        )
        self.inv_mass_second_moment_of_inertia = np.random.randn() * np.ones(
            (3, 3, self.n_elems)
        )
        self.shear_matrix = np.random.randn() * np.ones((3, 3, self.n_elems))

        # Things that are scalar mapped on voronoi
        self.voronoi_dilatation = np.random.rand(self.n_voronoi)
        self.rest_voronoi_lengths = np.random.rand(self.n_voronoi)

        # Things that are vectors mapped on voronoi
        self.kappa = np.random.randn(3, self.n_voronoi)
        self.rest_kappa = np.random.randn(3, self.n_voronoi)
        self.internal_couple = np.random.randn(3, self.n_voronoi)

        # Things that are matrix mapped on voronoi
        self.bend_matrix = np.random.randn() * np.ones((3, 3, self.n_voronoi))


@pytest.mark.parametrize("n_rods", [1, 2, 5, 6])
def test_construct_memory_block_structures_for_cosserat_rod(n_rods):
    """
    This test is only testing the validity of created block-structure class, using the
    construct_memory_block_structures function.

    Parameters
    ----------
    n_rods

    Returns
    -------

    """

    systems = [BaseRodForTesting(np.random.randint(10, 30 + 1)) for _ in range(n_rods)]

    memory_block_list = construct_memory_block_structures(systems)

    assert issubclass(memory_block_list[0].__class__, MemoryBlockCosseratRod)


@pytest.mark.parametrize("n_rods", [1, 2, 5, 6])
def test_memory_block_rod_straight_rods(n_rods):

    # Define a temporary list of systems
    n_elems = np.random.randint(low=10, high=31, size=(n_rods,))
    systems = [BaseRodForTesting(n_elems=n_elems[k]) for k in range(n_rods)]
    system_idx_list = np.arange(0, n_rods)

    # Initialize memory blocks
    memory_block = MemoryBlockCosseratRod(
        systems=systems, system_idx_list=system_idx_list
    )
    attr_list = dir(memory_block)

    # Test basic attributes
    assert memory_block.n_rods == n_rods

    start_idx_dict = {
        "node": memory_block.start_idx_in_rod_nodes.view(),
        "element": memory_block.start_idx_in_rod_elems.view(),
        "voronoi": memory_block.start_idx_in_rod_voronoi.view(),
    }

    end_idx_dict = {
        "node": memory_block.end_idx_in_rod_nodes.view(),
        "element": memory_block.end_idx_in_rod_elems.view(),
        "voronoi": memory_block.end_idx_in_rod_voronoi.view(),
    }

    expected_attr_dict = {
        "mass": "node",
        "position_collection": "node",
        "internal_forces": "node",
        "external_forces": "node",
        "radius": "element",
        "volume": "element",
        "density": "element",
        "lengths": "element",
        "rest_lengths": "element",
        "dilatation": "element",
        "dilatation_rate": "element",
        "tangents": "element",
        "sigma": "element",
        "rest_sigma": "element",
        "internal_torques": "element",
        "external_torques": "element",
        "internal_stress": "element",
        "director_collection": "element",
        "mass_second_moment_of_inertia": "element",
        "inv_mass_second_moment_of_inertia": "element",
        "shear_matrix": "element",
        "voronoi_dilatation": "voronoi",
        "rest_voronoi_lengths": "voronoi",
        "kappa": "voronoi",
        "rest_kappa": "voronoi",
        "internal_couple": "voronoi",
        "bend_matrix": "voronoi",
        "velocity_collection": "node",
        "omega_collection": "element",
        "acceleration_collection": "node",
        "alpha_collection": "element",
    }

    for attr, domain in expected_attr_dict.items():
        # Check if the memory block has the attribute
        assert attr in attr_list

        start_idx = start_idx_dict[domain]
        end_idx = end_idx_dict[domain]

        for k, system in enumerate(systems):
            block_view = memory_block.__dict__[attr].view()

            # Assert that the rod's and memory block's attributes share memory
            assert np.shares_memory(
                block_view[..., start_idx[k] : end_idx[k]], system.__dict__[attr]
            )

            # Assert that the rod's and memory block's attributes are equal in values
            assert np.all(
                system.__dict__[attr] == block_view[..., start_idx[k] : end_idx[k]]
            )
