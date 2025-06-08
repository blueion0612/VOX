package org.vox.capstonedesign1.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.vox.capstonedesign1.domain.Squad;

public interface SquadRepository extends JpaRepository<Squad, Long> {
}
