package org.vox.capstonedesign1.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.vox.capstonedesign1.domain.Squad;
import org.vox.capstonedesign1.dto.AgentSignalLogResponse;
import org.vox.capstonedesign1.dto.AgentViewResponse;
import org.vox.capstonedesign1.dto.SquadViewResponse;
import org.vox.capstonedesign1.service.AgentService;
import org.vox.capstonedesign1.service.SquadService;

import java.util.List;

@Slf4j
@Controller
@RequiredArgsConstructor
@RequestMapping("/squads")
public class AgentViewController {

    private final SquadService squadService;
    private final AgentService agentService;

    /**
     * [GET] /squads/{id}
     * 특정 소대의 요원 전체 상태 조회
     */
    @GetMapping("/{squadId}")
    public String getAllAgentStatusInSquad(@PathVariable Long squadId, Model model) {
        Squad squad = squadService.findById(squadId);
        SquadViewResponse squadViewResponse = new SquadViewResponse(squad);
        List<AgentViewResponse> statuses = agentService.getAgentStatusesBySquadId(squadId);
        model.addAttribute("squad", squadViewResponse);
        model.addAttribute("statuses", statuses);
        return "squadDetail";
    }

    // 1초마다 요약 정보를 가져오는 REST API (JSON 반환)
    @ResponseBody
    @GetMapping("/{squadId}/agent-status")
    public List<AgentViewResponse> getSquadAgentStatus(@PathVariable Long squadId) {
        return agentService.getAgentStatusesBySquadId(squadId);
    }

    // 1초마다 로그 정보를 누적해서 가져오는 REST API (JSON 반환)
    @ResponseBody
    @GetMapping("/{squadId}/logs")
    public List<AgentSignalLogResponse> getSquadLogs(@PathVariable Long squadId) {
        // 최근 N건 누적 로그 가져오는 서비스 메소드 만들어서 호출
        return agentService.getSquadAgentLogs(squadId); // 아래 AgentService 참고
    }
}
