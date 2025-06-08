package org.vox.capstonedesign1.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class UnityViewController {
    @GetMapping("/unity-view/{deviceSerialNumber}")
    public String renderUnityView(@PathVariable String deviceSerialNumber, Model model) {
        model.addAttribute("deviceSerialNumber", deviceSerialNumber);
        return "unity-view";
    }
}
