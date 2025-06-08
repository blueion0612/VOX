package org.vox.capstonedesign1.util.handler;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
@RequiredArgsConstructor
public class UnityWebSocketHandler extends TextWebSocketHandler {

    private final Map<String, WebSocketSession> deviceSessions = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        String deviceSerialNumber = getDeviceSerialFromQuery(session.getUri().toString());
        if (deviceSerialNumber != null) {
            deviceSessions.put(deviceSerialNumber, session);
            log.info("WebSocket 연결됨: {}", deviceSerialNumber);
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        deviceSessions.entrySet().removeIf(entry -> entry.getValue().equals(session));
        log.info("WebSocket 연결 종료됨: {}", session.getId());
    }

    public void sendTextToDevice(String deviceSerialNumber, String message) {
        WebSocketSession session = deviceSessions.get(deviceSerialNumber);
        if (session != null && session.isOpen()) {
            try {
                session.sendMessage(new TextMessage(message));
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private String getDeviceSerialFromQuery(String uri) {
        if (uri.contains("deviceSerialNumber=")) {
            return uri.split("deviceSerialNumber=")[1];
        }
        return null;
    }
}
