using Listener;
using System.Runtime.InteropServices;
using System;
using UnityEngine;

public class WebSocketBridge : MonoBehaviour
{
    [DllImport("__Internal")]
    private static extern void ConnectWebSocket();

    [SerializeField] private FreeHips hipsTarget;

    void Start()
    {
#if UNITY_WEBGL && !UNITY_EDITOR
        ConnectWebSocket();
#endif
        if (hipsTarget == null)
            Debug.LogWarning("hipsTarget is not assigned!");
    }

    public void OnReceiveWebSocket(string msg)
    {
        Debug.Log("[Unity] Received WS: " + msg);
        var floats = Array.ConvertAll(msg.Split(','), float.Parse);
        hipsTarget?.ApplyPoseData(floats);
    }
}
