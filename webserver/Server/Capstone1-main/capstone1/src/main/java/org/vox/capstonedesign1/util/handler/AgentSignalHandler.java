package org.vox.capstonedesign1.util.handler;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.vox.capstonedesign1.dto.AgentSignalRequest;
import org.vox.capstonedesign1.service.AgentSignalService;
import org.vox.capstonedesign1.service.DeviceService;
import org.vox.capstonedesign1.util.calculator.FrequencyCalculator;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static java.util.stream.StreamSupport.stream;

@Slf4j
@Component
@RequiredArgsConstructor
public class AgentSignalHandler implements UdpMessageHandler {

    private final AgentSignalService agentSignalService;
    private final DeviceService deviceService;
    private final UnityWebSocketHandler unityWebSocketHandler;
    private final FrequencyCalculator frequencyCalculator;

    @Override
    public void handleMessage(byte[] data) {
        ByteBuffer buffer = extractInformation(data);
        saveSignal(buffer);
    }

    private ByteBuffer extractInformation(byte[] data) {
        log.info("수신된 UDP 데이터 길이: {}", data.length);
        return ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
    }

    private void saveSignal(ByteBuffer buffer) {
        double timestamp = buffer.getDouble();
        Long deviceId = (long) buffer.getInt();
        Long statusId = (long) buffer.getInt() + 1;
        log.info("수신된 UDP 데이터: timestamp={}, deviceId={}, statusId={}", timestamp, deviceId, statusId);
        long seconds = (long) timestamp;
        long nanos = (long) ((timestamp % 1) * 1_000_000_000);  // 소수점 이하 나노초
        Instant instant = Instant.ofEpochSecond(seconds, nanos);
        LocalDateTime localTimestamp = instant.atZone(ZoneId.of("Asia/Seoul")).toLocalDateTime();
        String formattedTimestamp = localTimestamp.format(DateTimeFormatter.ISO_DATE_TIME);
        log.info("수신된 시간: formattedTimestamp={}", timestamp);
        String deviceSerialNumber = deviceService.resolveDeviceSerialNumber(deviceId);
        // frequency 계산
        double frequency = frequencyCalculator.calculateFrequency(deviceSerialNumber, timestamp);
        // 저장 요청 객체 생성
        AgentSignalRequest request = AgentSignalRequest.builder()
                .deviceSerialNumber(deviceSerialNumber)
                .statusId(statusId)
                .timeStamp(formattedTimestamp)
                .streamingFrequency(frequency)
                .build();
        // DB 저장
        agentSignalService.saveSignal(request);
    }
}
