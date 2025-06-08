package org.vox.capstonedesign1.util.calculator;

import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class FrequencyCalculator {

    private final Map<String, Double> lastTimestamps = new ConcurrentHashMap<>();

    private double frequency = 0.0;

    public double calculateFrequency(String deviceSerialNumber, double currentTimestamp) {
        Double previousTimestamp = lastTimestamps.get(deviceSerialNumber);
        if (previousTimestamp == null) {
            return frequency;
        }
        double timeDiff = currentTimestamp - previousTimestamp;
        if (timeDiff > 0) {
            frequency = 1.0 / timeDiff;
        } else {
            frequency = 0.0; // timestamp가 같거나 과거일 경우
        }
        // 현재 timestamp 갱신
        lastTimestamps.put(deviceSerialNumber, currentTimestamp);
        return frequency;
    }
}
