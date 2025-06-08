package org.vox.capstonedesign1.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.vox.capstonedesign1.domain.Agent;

import java.util.List;
import java.util.Optional;

public interface AgentRepository extends JpaRepository<Agent, Long> {
    Optional<Agent> findByDevice_DeviceSerialNumber(String deviceSerialNumber);
    List<Agent> findBySquad_IdOrderById(Long squadId);
}
