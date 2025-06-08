package org.vox.capstonedesign1.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.vox.capstonedesign1.domain.Agent;
import org.vox.capstonedesign1.domain.AgentSignal;

import java.util.List;
import java.util.Optional;

public interface AgentSignalRepository extends JpaRepository<AgentSignal, Long> {
    List<AgentSignal> findByAgentInOrderByTimeStampDesc(List<Agent> agents);
    Optional<AgentSignal> findTopByAgentOrderByTimeStampDesc(Agent agent);
}
