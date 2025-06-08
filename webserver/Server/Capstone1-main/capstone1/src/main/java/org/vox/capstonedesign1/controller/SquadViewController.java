package org.vox.capstonedesign1.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.vox.capstonedesign1.dto.SquadViewResponse;
import org.vox.capstonedesign1.service.SquadService;

import java.util.List;

@Controller
@RequiredArgsConstructor
@RequestMapping("/squads")
public class SquadViewController {

    private final SquadService squadService;

    /**
     * [GET] /squads
     * 전체 소대 목록 조회
     */
    @GetMapping
    public String findAllSquads(Model model) {
        List<SquadViewResponse> squads = squadService.findAll()
                .stream()
                .map(SquadViewResponse::new)
                .toList();
        model.addAttribute("squads", squads);
        return "squadList";
    }
}
