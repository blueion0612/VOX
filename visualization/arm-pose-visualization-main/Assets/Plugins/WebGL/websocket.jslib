mergeInto(LibraryManager.library, {
  ConnectWebSocket: function () {
    var socket = new WebSocket("wss://voxkr.xyz/ws/unity?deviceSerialNumber=abc123");

    socket.onmessage = function (event) {
      SendMessage("WebSocketReceiver", "OnReceiveWebSocket", event.data);
    };

    socket.onopen = function () {
      console.log("WebSocket connected.");
    };

    socket.onerror = function (e) {
      console.error("WebSocket error", e);
    };

    socket.onclose = function () {
      console.warn("WebSocket closed.");
    };
  }
});

