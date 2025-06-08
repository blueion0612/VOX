package org.vox.capstonedesign1.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class StreamController {
    @GetMapping("/squads/{squadId}/{serial}/hls")
    public String hlsPlayer(@PathVariable Long squadId, @PathVariable String serial, Model model) {
        model.addAttribute("streamKey", serial);
        return "hlsPlayer";
    }
}
