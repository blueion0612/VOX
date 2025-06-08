package org.vox.capstonedesign1.dto;

import lombok.Getter;
import org.vox.capstonedesign1.domain.Squad;

@Getter
public class SquadViewResponse {

    private final Long id;
    private final String squadName;

    public SquadViewResponse(Squad squad) {
        this.id = squad.getId();
        this.squadName = squad.getSquadName();
    }
}
