import os
import numpy as np
import pypsa

def normed(s): return s/s.sum()

def test_pf_distributed_slack():
    csv_folder_name = os.path.join(os.path.dirname(__file__), "..",
                      "examples", "scigrid-de", "scigrid-with-load-gen-trafos")

    network = pypsa.Network(csv_folder_name)
    network.set_snapshots(network.snapshots[:2])

    #There are some infeasibilities without line extensions
    network.lines.s_max_pu = 0.7
    network.lines.loc[["316","527","602"],"s_nom"] = 1715
    network.storage_units.state_of_charge_initial = 0.

    network.lopf(network.snapshots, solver_name='cbc', formulation='kirchhoff')

    #For the PF, set the P to the optimised P
    network.generators_t.p_set = network.generators_t.p
    network.storage_units_t.p_set = network.storage_units_t.p

    #set all buses to PV, since we don't know what Q set points are
    network.generators.control = "PV"

    #Need some PQ buses so that Jacobian doesn't break
    f = network.generators[network.generators.bus == "492"]
    network.generators.loc[f.index,"control"] = "PQ"

    network.pf(distribute_slack=True)

    np.testing.assert_array_almost_equal(
        network.generators_t.p_set.apply(normed, axis=1),
        (network.generators_t.p - network.generators_t.p_set).apply(normed, axis=1)
    )


if __name__ == "__main__":
    test_pf_distributed_slack()
