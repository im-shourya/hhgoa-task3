// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title EvidenceRegistry
/// @notice The smart contract anchors a cryptographic fingerprint; it does not independently prove that the underlying face identification or web-search result is truthful.
contract EvidenceRegistry {
    struct Record {
        uint256 timestamp;
        address submitter;
    }

    // Mapping from a SHA-256 evidence fingerprint (bytes32) to its registration Record.
    mapping(bytes32 => Record) private _records;

    event EvidenceRegistered(
        bytes32 indexed fingerprint,
        address indexed submitter,
        uint256 timestamp
    );

    error EvidenceAlreadyExists(bytes32 fingerprint);
    error InvalidEvidenceHash();

    /// @notice Anchors a cryptographic evidence fingerprint on-chain.
    /// @param fingerprint The 32-byte SHA-256 hash of the canonical evidence manifest.
    function registerEvidence(bytes32 fingerprint) external {
        if (fingerprint == bytes32(0)) {
            revert InvalidEvidenceHash();
        }

        if (_records[fingerprint].timestamp != 0) {
            revert EvidenceAlreadyExists(fingerprint);
        }

        _records[fingerprint] = Record({
            timestamp: block.timestamp,
            submitter: msg.sender
        });

        emit EvidenceRegistered(
            fingerprint,
            msg.sender,
            block.timestamp
        );
    }

    /// @notice Retrieves the anchored record for a specific evidence fingerprint.
    /// @param fingerprint The 32-byte SHA-256 hash of the canonical evidence manifest.
    /// @return exists Boolean indicating whether the evidence is registered.
    /// @return timestamp The block timestamp when the evidence was registered.
    /// @return submitter The address that submitted the evidence.
    function getEvidence(bytes32 fingerprint)
        external
        view
        returns (
            bool exists,
            uint256 timestamp,
            address submitter
        )
    {
        Record memory record = _records[fingerprint];
        return (
            record.timestamp != 0,
            record.timestamp,
            record.submitter
        );
    }

    /// @notice Checks if an evidence fingerprint has been registered.
    /// @param fingerprint The 32-byte SHA-256 hash of the canonical evidence manifest.
    /// @return True if registered, false otherwise.
    function evidenceExists(bytes32 fingerprint) external view returns (bool) {
        return _records[fingerprint].timestamp != 0;
    }
}
