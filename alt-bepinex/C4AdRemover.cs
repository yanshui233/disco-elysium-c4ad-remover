// C4AdRemover — 运行时销毁 Disco Elysium 的 ZERO PARADES 广告对象
// 目标: BepInEx 6 (Bleeding Edge) — Unity IL2CPP，x64
//
// 与 c4ad_mod.py 的区别:
//   c4ad_mod.py  = 把 C4Ad 的 RectTransform 移出屏幕（改资源文件），无需任何 loader，
//                  但游戏更新后要重打。注意：直接改 m_IsActive=0 是无效的，游戏会在
//                  运行时把它重新激活。
//   本插件       = 运行时 GameObject.Find("C4Ad") 后 Destroy（并轮询兜底重实例化），
//                  游戏更新后依然生效
//
// 状态: 未编译 / 未测试。构建步骤见同目录 BUILD.md

using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using UnityEngine;

namespace DiscoNoAds
{
    [BepInPlugin(Guid, "C4Ad Remover", "1.0.0")]
    public class Plugin : BasePlugin
    {
        public const string Guid = "local.disco.c4ad-remover";
        internal static ManualLogSource Logger;

        public override void Load()
        {
            Logger = Log;
            AddComponent<AdKiller>();
            Logger.LogInfo("C4Ad Remover loaded - ZERO PARADES banner will be destroyed.");
        }
    }

    public class AdKiller : MonoBehaviour
    {
        // C4Ad 位于常驻场景 Init.unity 的 Global UI Canvas 下，
        // 场景切换时不会被销毁，所以低频轮询足够，也顺便兜住它被重新实例化的情况。
        private float _timer;
        private const float Interval = 0.5f;

        private void Update()
        {
            _timer += Time.deltaTime;
            if (_timer < Interval) return;
            _timer = 0f;
            TryKill();
        }

        private static void TryKill()
        {
            var go = GameObject.Find("C4Ad");
            if (go == null) return;
            Object.Destroy(go);
            Plugin.Logger.LogInfo("C4Ad destroyed.");
        }
    }
}
