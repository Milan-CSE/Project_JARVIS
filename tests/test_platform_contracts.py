from __future__ import annotations

import unittest

from ai_os.platform import (
    PlatformBoundary,
    PlatformComponent,
    PlatformComponentDescriptor,
    PlatformContract,
)


class ValidComponent:
    def __init__(self, descriptor: PlatformComponentDescriptor) -> None:
        self._descriptor = descriptor

    @property
    def descriptor(self) -> PlatformComponentDescriptor:
        return self._descriptor


class InvalidComponent:
    pass


class ValidBoundary:
    def __init__(self, contract: PlatformContract) -> None:
        self._contract = contract

    @property
    def contract(self) -> PlatformContract:
        return self._contract


class InvalidBoundary:
    pass


class PlatformContractTests(unittest.TestCase):
    def create_contract(self) -> PlatformContract:
        return PlatformContract(
            platform_id="ai-os",
            version="0.1.0",
            metadata={"stage": "platform"},
        )

    def create_descriptor(self) -> PlatformComponentDescriptor:
        return PlatformComponentDescriptor(
            component_id="config",
            version="1.0.0",
            component_type="service",
            metadata={"scope": "platform"},
        )

    def test_platform_contract_matches_expected_shape(self) -> None:
        contract = self.create_contract()

        self.assertEqual(contract.platform_id, "ai-os")
        self.assertEqual(contract.version, "0.1.0")

    def test_platform_contract_is_immutable(self) -> None:
        contract = self.create_contract()

        with self.assertRaises(AttributeError):
            contract.version = "2.0.0"

    def test_platform_contract_metadata_is_immutable(self) -> None:
        contract = self.create_contract()

        with self.assertRaises(TypeError):
            contract.metadata["stage"] = "changed"

    def test_platform_contract_copies_input_mapping(self) -> None:
        metadata = {"x": 1}
        contract = PlatformContract(
            platform_id="ai-os",
            version="0.1.0",
            metadata=metadata,
        )

        metadata["x"] = 2

        self.assertEqual(contract.metadata["x"], 1)

    def test_empty_platform_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PlatformContract(
                platform_id="",
                version="0.1.0",
            )

    def test_whitespace_platform_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PlatformContract(
                platform_id="   ",
                version="0.1.0",
            )

    def test_non_string_platform_id_rejected(self) -> None:
        with self.assertRaises(TypeError):
            PlatformContract(
                platform_id=123,
                version="0.1.0",
            )

    def test_empty_version_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PlatformContract(
                platform_id="ai-os",
                version="",
            )

    def test_non_string_version_rejected(self) -> None:
        with self.assertRaises(TypeError):
            PlatformContract(
                platform_id="ai-os",
                version=123,
            )

    def test_invalid_metadata_rejected(self) -> None:
        with self.assertRaises(TypeError):
            PlatformContract(
                platform_id="ai-os",
                version="0.1.0",
                metadata=[],
            )

    def test_descriptor_matches_expected_shape(self) -> None:
        descriptor = self.create_descriptor()

        self.assertEqual(descriptor.component_id, "config")
        self.assertEqual(descriptor.version, "1.0.0")
        self.assertEqual(descriptor.component_type, "service")

    def test_descriptor_is_immutable(self) -> None:
        descriptor = self.create_descriptor()

        with self.assertRaises(AttributeError):
            descriptor.component_id = "other"

    def test_descriptor_metadata_is_immutable(self) -> None:
        descriptor = self.create_descriptor()

        with self.assertRaises(TypeError):
            descriptor.metadata["scope"] = "other"

    def test_descriptor_copies_input_mapping(self) -> None:
        metadata = {"x": 1}
        descriptor = PlatformComponentDescriptor(
            component_id="config",
            version="1.0.0",
            component_type="service",
            metadata=metadata,
        )

        metadata["x"] = 2

        self.assertEqual(descriptor.metadata["x"], 1)

    def test_empty_component_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PlatformComponentDescriptor(
                component_id="",
                version="1.0.0",
                component_type="service",
            )

    def test_empty_component_type_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PlatformComponentDescriptor(
                component_id="config",
                version="1.0.0",
                component_type="",
            )

    def test_invalid_descriptor_metadata_rejected(self) -> None:
        with self.assertRaises(TypeError):
            PlatformComponentDescriptor(
                component_id="config",
                version="1.0.0",
                component_type="service",
                metadata=[],
            )

    def test_valid_component_matches_protocol(self) -> None:
        component = ValidComponent(self.create_descriptor())

        self.assertIsInstance(component, PlatformComponent)

    def test_invalid_component_does_not_match_protocol(self) -> None:
        self.assertFalse(
            isinstance(InvalidComponent(), PlatformComponent)
        )

    def test_valid_boundary_matches_protocol(self) -> None:
        boundary = ValidBoundary(self.create_contract())

        self.assertIsInstance(boundary, PlatformBoundary)

    def test_invalid_boundary_does_not_match_protocol(self) -> None:
        self.assertFalse(
            isinstance(InvalidBoundary(), PlatformBoundary)
        )

    def test_component_contract_contains_no_execution_api(self) -> None:
        descriptor = self.create_descriptor()

        self.assertFalse(hasattr(descriptor, "execute"))
        self.assertFalse(hasattr(descriptor, "run"))
        self.assertFalse(hasattr(descriptor, "reason"))
        self.assertFalse(hasattr(descriptor, "plan"))

    def test_platform_contract_contains_no_registry_api(self) -> None:
        contract = self.create_contract()

        self.assertFalse(hasattr(contract, "register"))
        self.assertFalse(hasattr(contract, "resolve"))
        self.assertFalse(hasattr(contract, "unregister"))

    def test_contracts_do_not_contain_identity_or_security_authority(self) -> None:
        contract = self.create_contract()
        descriptor = self.create_descriptor()

        for value in (contract, descriptor):
            self.assertFalse(hasattr(value, "identity"))
            self.assertFalse(hasattr(value, "principal"))
            self.assertFalse(hasattr(value, "authorize"))
            self.assertFalse(hasattr(value, "permissions"))

    def test_contracts_do_not_depend_on_runtime_or_tools(self) -> None:
        contract = self.create_contract()
        descriptor = self.create_descriptor()

        for value in (contract, descriptor):
            self.assertFalse(hasattr(value, "runtime_executor"))
            self.assertFalse(hasattr(value, "task_registry"))
            self.assertFalse(hasattr(value, "tool_registry"))
            self.assertFalse(hasattr(value, "workflow_runner"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
