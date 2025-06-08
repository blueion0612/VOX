package org.vox.capstonedesign1.service;

import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.vox.capstonedesign1.domain.Squad;
import org.vox.capstonedesign1.repository.SquadRepository;

import java.util.List;

@Service
@RequiredArgsConstructor
public class SquadService {

    private final SquadRepository squadRepository;

    public Squad findById(Long id) {
        return squadRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Squad not found"));
    }

    public List<Squad> findAll() {
        return squadRepository.findAll();
    }
}
