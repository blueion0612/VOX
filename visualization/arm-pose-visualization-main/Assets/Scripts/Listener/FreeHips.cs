using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using UnityEngine;

namespace Listener
{
    public class FreeHips : Basis
    {
        // Computation Shader Visualisation Objects
        [SerializeField] private Material mcPredMaterial;
        [SerializeField] private Mesh mcPredMesh;

        // Streaming Parameters
        [SerializeField] private int port = 50003;
        [SerializeField] private bool leftHandMode = true;

        // Reference GameObject
        [SerializeField] private GameObject hips;

        // Computation Shader Parameters
        private static readonly int
            PositionsId = Shader.PropertyToID("_Positions"),
            ScaleId = Shader.PropertyToID("_Scale"),
            OrigId = Shader.PropertyToID("_Origin"),
            UarmId = Shader.PropertyToID("_Uarm"),
            LarmId = Shader.PropertyToID("_Larm"),
            HandId = Shader.PropertyToID("_Hand");

        private byte[] _msgTail;
        private ComputeBuffer _positionsBuffer;
        private Bounds _bounds = new(Vector3.zero, Vector3.one * 5f);
        private int _cubeCount;


        private Thread _udpListenerThread;
        private UdpClient _udpClient;
        private bool _pause;

        private Quaternion _handRot;
        private Vector3 _handPos;
        private Quaternion _larmRot;
        private Vector3 _larmPos;
        private Quaternion _uarmRot;
        private Vector3 _uarmPos;
        private Quaternion _hipsRot;

        // Start is called before the first frame update
        private void Start()
        {
            _udpListenerThread = new Thread(UDPListener);
            _udpListenerThread.Start();
            mcPredMaterial.SetFloat(ScaleId, 0.01f);
        }

        private void UDPListener()
        {
            //Creates a UdpClient for reading incoming data.
            _udpClient = new UdpClient(port);
            //Creates an IPEndPoint to record the IP Address and port number of the sender.
            var remoteIpEndPoint = new IPEndPoint(IPAddress.Any, 0);

            Debug.Log("start listening");
            while (true)
            {
                if (_pause)
                {
                    Thread.Sleep(100);
                    continue;
                }

                // Blocks until a message returns on this socket from a remote host.
                var msg = _udpClient.Receive(ref remoteIpEndPoint);

                // the basic message
                _handRot = new Quaternion(
                    BitConverter.ToSingle(msg, 4),
                    BitConverter.ToSingle(msg, 8),
                    BitConverter.ToSingle(msg, 12),
                    BitConverter.ToSingle(msg, 0)
                );
                Debug.Log($"[FreeHips] Hand ROT (quaternion): {_handRot}");
                _handPos = new Vector3(
                    BitConverter.ToSingle(msg, 16),
                    BitConverter.ToSingle(msg, 20),
                    BitConverter.ToSingle(msg, 24)
                );
                _larmRot = new Quaternion(
                    BitConverter.ToSingle(msg, 32),
                    BitConverter.ToSingle(msg, 36),
                    BitConverter.ToSingle(msg, 40),
                    BitConverter.ToSingle(msg, 28)
                );
                _larmPos = new Vector3(
                    BitConverter.ToSingle(msg, 44),
                    BitConverter.ToSingle(msg, 48),
                    BitConverter.ToSingle(msg, 52)
                );
                _uarmRot = new Quaternion(
                    BitConverter.ToSingle(msg, 60),
                    BitConverter.ToSingle(msg, 64),
                    BitConverter.ToSingle(msg, 68),
                    BitConverter.ToSingle(msg, 56)
                );
                _uarmPos = new Vector3(
                    BitConverter.ToSingle(msg, 72),
                    BitConverter.ToSingle(msg, 76),
                    BitConverter.ToSingle(msg, 80)
                );
                _hipsRot = new Quaternion(
                    BitConverter.ToSingle(msg, 88),
                    BitConverter.ToSingle(msg, 92),
                    BitConverter.ToSingle(msg, 96),
                    BitConverter.ToSingle(msg, 84)
                );

                // if the message is longer, we have additional monte carlo predictions
                // store tail to pass to compute shader
                if (msg.Length > 100)
                    _msgTail = msg.Skip(100).ToArray();
            }
        }

        //public override void MoveBoneMap(Dictionary<string, GameObject> boneMap)
        //{
        //    var hipsPos = hips.transform.position;
        //    boneMap["Hips"].transform.rotation = _hipsRot;

        //    if (leftHandMode)
        //    {
        //        boneMap["LeftHand"].transform.SetPositionAndRotation(_handPos + hipsPos, _handRot);
        //        boneMap["LeftLowerArm"].transform.SetPositionAndRotation(_larmPos + hipsPos, _larmRot);
        //        boneMap["LeftUpperArm"].transform.SetPositionAndRotation(_uarmPos + hipsPos, _uarmRot);
        //    }
        //    else
        //    {
        //        boneMap["RightHand"].transform.SetPositionAndRotation(_handPos + hipsPos, _handRot);
        //        boneMap["RightLowerArm"].transform.SetPositionAndRotation(_larmPos + hipsPos, _larmRot);
        //        boneMap["RightUpperArm"].transform.SetPositionAndRotation(_uarmPos + hipsPos, _uarmRot);
        //    }
        //    // for finding reason of motionerror
        //    Debug.Log($"[FreeHips] UarmRot: {_uarmRot}, LarmRot: {_larmRot}, HandRot: {_handRot}");
        //    Debug.Log($"[FreeHips] UarmPos: {_larmPos}, HandPos: {_handPos}");

        //    // now the positions buffer for our monte carlo hand and larm positions
        //    if (_msgTail is not null)
        //    {
        //        // create a new buffer if non was created yet or if the size changed
        //        if (_positionsBuffer is null || _positionsBuffer.count != _msgTail.Count())
        //        {
        //            _positionsBuffer = new ComputeBuffer(_msgTail.Count(), 3 * 4);
        //            _cubeCount = _positionsBuffer.count / 12;
        //            Debug.Log("Created positions buffer with count " +
        //                      _positionsBuffer.count + " (" + _cubeCount +
        //                      " cubes)");
        //        }

        //        // write positions to buffer
        //        _positionsBuffer.SetData(_msgTail);

        //        // we add the shoulder position to predicted positions on the GPU 
        //        mcPredMaterial.SetVector(OrigId, hipsPos);
        //        mcPredMaterial.SetVector(UarmId, _uarmPos);
        //        mcPredMaterial.SetVector(LarmId, _larmPos);
        //        mcPredMaterial.SetVector(HandId, _handPos);
        //        mcPredMaterial.SetBuffer(PositionsId, _positionsBuffer);

        //        // instantiate cubes 
        //        Graphics.DrawMeshInstancedProcedural(
        //            mcPredMesh, 0, mcPredMaterial, _bounds, _cubeCount
        //        );
        //    }
        //}

        public override void MoveBoneMap(Dictionary<string, GameObject> boneMap)
        {
            var hipsPos = hips.transform.position;
            boneMap["Hips"].transform.rotation = _hipsRot;

            if (leftHandMode)
            {
                boneMap["LeftHand"].transform.SetPositionAndRotation(_handPos + hipsPos, _handRot);
                boneMap["LeftLowerArm"].transform.SetPositionAndRotation(_larmPos + hipsPos, _larmRot);
                boneMap["LeftUpperArm"].transform.SetPositionAndRotation(_uarmPos + hipsPos, _uarmRot);
            }
            else
            {
                boneMap["RightHand"].transform.SetPositionAndRotation(_handPos + hipsPos, _handRot);
                boneMap["RightLowerArm"].transform.SetPositionAndRotation(_larmPos + hipsPos, _larmRot);
                boneMap["RightUpperArm"].transform.SetPositionAndRotation(_uarmPos + hipsPos, _uarmRot);
            }

            Debug.Log($"[FreeHips] UarmRot: {_uarmRot}, LarmRot: {_larmRot}, HandRot: {_handRot}");
            Debug.Log($"[FreeHips] UarmPos: {_larmPos}, HandPos: {_handPos}");

            if (_msgTail is not null)
            {
                if (_positionsBuffer is null || _positionsBuffer.count != _msgTail.Count())
                {
                    _positionsBuffer = new ComputeBuffer(_msgTail.Count(), 3 * 4);
                    _cubeCount = _positionsBuffer.count / 12;
                    Debug.Log("Created positions buffer with count " + _positionsBuffer.count + " (" + _cubeCount + " cubes)");
                }

                _positionsBuffer.SetData(_msgTail);

                mcPredMaterial.SetVector(OrigId, hipsPos);
                mcPredMaterial.SetVector(UarmId, _uarmPos);
                mcPredMaterial.SetVector(LarmId, _larmPos);
                mcPredMaterial.SetVector(HandId, _handPos);
                mcPredMaterial.SetBuffer(PositionsId, _positionsBuffer);

                Graphics.DrawMeshInstancedProcedural(mcPredMesh, 0, mcPredMaterial, _bounds, _cubeCount);
            }
        }


        public void ApplyPoseData(float[] f)
        {
            if (f.Length < 25)
            {
                Debug.LogWarning("[FreeHips] Insufficient data received via WebSocket.");
                return;
            }

            //Quaternion fixX = Quaternion.Euler(180, 0, 0);                              // X 반전 (뒤집힘 보정)
            //Quaternion fixY = Quaternion.Euler(0, 180, 0);                              // Y 반전
            //Quaternion fixZ = Quaternion.Euler(0, 0, 180);                              // Z 반전
            //Quaternion wristFix = Quaternion.Euler(0, 0, 45);                           // 손목 약간 회전 보정

            //_handRot = fixX * new Quaternion(f[0], f[1], f[2], f[3]) * wristFix;
            
            //Quaternion fix = Quaternion.Euler(180, 0, 45);                              // 이전 해결 당시 코드
            //_handRot = fix * new Quaternion(f[0], f[1], f[2], f[3]) * wristFix;

            
            //Vector3 MirrorY(Vector3 v) => new Vector3(v.x, -v.y, v.z);                  // Y축 반전 (위아래 뒤집기)
                        
            //Vector3 MirrorZ(Vector3 v) => new Vector3(v.x, v.y, -v.z);                  // Z축 반전 (전후 반전)
                      
            //Vector3 MirrorX(Vector3 v) => new Vector3(-v.x, v.y, v.z);                  // X축 반전 (좌우 반전)




            _handRot = new Quaternion(f[0], f[1], f[2], f[3]);
            _handPos = new Vector3(f[4], f[5], f[6]);

            _larmRot = new Quaternion(f[7], f[8], f[9], f[10]);
            _larmPos = new Vector3(f[11], f[12], f[13]);

            _uarmRot = new Quaternion(f[14], f[15], f[16], f[17]);
            _uarmPos = new Vector3(f[18], f[19], f[20]);

            _hipsRot = new Quaternion(f[21], f[22], f[23], f[24]);

            Debug.Log("[FreeHips] WebSocket pose applied (raw, no correction).");
        }






        private void Update()
        {
            if (Input.GetKeyDown("space"))
            {
                _pause = !_pause;
                Debug.Log("Pause " + _pause);
            }
        }
    }
}