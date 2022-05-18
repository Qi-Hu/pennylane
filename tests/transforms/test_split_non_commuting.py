# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Tests for the transform ``qml.transform.split_non_commuting()`` """
import pytest
import numpy as np
import pennylane as qml

from pennylane.transforms import split_non_commuting


# Unit tests for split_non_commuting


def test_commuting_group_no_split():
    """Testing that commuting groups are not split"""
    with qml.tape.QuantumTape() as tape:
        qml.PauliZ(0)
        qml.Hadamard(0)
        qml.CNOT((0, 1))
        qml.expval(qml.PauliZ(0))
        qml.expval(qml.PauliZ(0))
        qml.expval(qml.PauliX(1))
        qml.expval(qml.PauliZ(2))
        qml.expval(qml.PauliZ(0) @ qml.PauliZ(3))

    split, fn = split_non_commuting(tape)

    assert split == [tape]
    assert all([isinstance(t, qml.tape.QuantumTape) for t in split])
    assert (
        fn([0.5]) == 0.5
    )  # is there a better way to assert that fn is just taking the first element of what ever it is input?


### example tape with 3 commuting groups [[0,3],[1,4],[2,5]]
with qml.tape.QuantumTape() as non_commuting_tape3:
    qml.PauliZ(0)
    qml.Hadamard(0)
    qml.CNOT((0, 1))
    qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))
    qml.expval(qml.PauliX(0) @ qml.PauliX(1))
    qml.expval(qml.PauliY(0) @ qml.PauliY(1))
    qml.expval(qml.PauliZ(0))
    qml.expval(qml.PauliX(0))
    qml.expval(qml.PauliY(0))

### example tape with 2 -commuting groups [[0,2],[1,3]]
with qml.tape.QuantumTape() as non_commuting_tape2:
    qml.PauliZ(0)
    qml.Hadamard(0)
    qml.CNOT((0, 1))
    qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))
    qml.expval(qml.PauliX(0) @ qml.PauliX(1))
    qml.expval(qml.PauliZ(0))
    qml.expval(qml.PauliX(0))

non_commuting_tapes = [non_commuting_tape2, non_commuting_tape3]


@pytest.mark.parametrize("tape,expected", [(non_commuting_tape2, 2), (non_commuting_tape3, 3)])
def test_non_commuting_group_right_number(tape, expected):
    """Test that the output is of the correct size"""
    split, _ = split_non_commuting(tape)
    assert len(split) == expected


@pytest.mark.parametrize(
    "tape,group_coeffs",
    [(non_commuting_tape2, [[0, 2], [1, 3]]), (non_commuting_tape3, [[0, 3], [1, 4], [2, 5]])],
)
def test_non_commuting_group_right_reorder(tape, group_coeffs):
    """Test that the output is of the correct size"""
    split, fn = split_non_commuting(tape)
    assert all(np.array(fn(group_coeffs)) == np.arange(len(split) * 2))


### Test for other measurement types

obs_fn = [qml.expval, qml.var, qml.sample]


@pytest.mark.parametrize("meas_type", obs_fn)
def test_different_measurement_types(meas_type):
    """Test that expval, var and sample are correctly reproduced"""
    with qml.tape.QuantumTape() as tape:
        qml.PauliZ(0)
        qml.Hadamard(0)
        qml.CNOT((0, 1))
        meas_type(qml.PauliZ(0) @ qml.PauliZ(1))
        meas_type(qml.PauliX(0) @ qml.PauliX(1))
        meas_type(qml.PauliZ(0))
        meas_type(qml.PauliX(0))
    the_return_type = tape.measurements[0].return_type
    split, _ = split_non_commuting(tape)
    for new_tape in split:
        for meas in new_tape.measurements:
            assert meas.return_type == the_return_type


## Testing in context of qnode with groups of non-commuting observables


def test_expval_non_commuting_observables():
    """Test expval with multiple non-commuting operators"""
    dev = qml.device("default.qubit", wires=5)

    @qml.qnode(dev)
    def circuit():
        qml.Hadamard(1)
        qml.Hadamard(0)
        qml.PauliZ(0)
        qml.Hadamard(3)
        return [
            qml.expval(qml.PauliZ(0) @ qml.PauliZ(1)),
            qml.expval(qml.PauliX(0)),
            qml.expval(qml.PauliZ(1)),
            qml.expval(qml.PauliX(1) @ qml.PauliX(4)),
            qml.expval(qml.PauliX(3)),
        ]

    assert all(np.isclose(circuit(), np.array([0.0, -1.0, 0.0, 0.0, 1.0])))


# Autodiff tests

# @pytest.mark.jax
