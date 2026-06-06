using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Text;

internal static class HermesZhCNSetup
{
    private const string DefaultBaseUrl = "https://useai.live/hermes";
    private const string DefaultFallbackBaseUrl = "https://cdn.jsdelivr.net/gh/fresh-claw/hermes-cn@v2026.06.05.2";

    private static int Main()
    {
        try
        {
            Console.OutputEncoding = Encoding.UTF8;
        }
        catch
        {
            // Older Windows consoles may reject UTF-8; continue with the default encoding.
        }

        Console.Title = "Hermes 中文增强安装器";
        Console.WriteLine("Hermes 中文增强安装器");
        Console.WriteLine();
        Console.WriteLine("将安装官方 Hermes 桌面端，并应用中文增强。");
        Console.WriteLine();

        var baseUrl = GetEnv("XIAOMA_HERMES_BASE_URL", DefaultBaseUrl).TrimEnd('/');
        var fallbackBaseUrl = GetEnv("XIAOMA_HERMES_FALLBACK_BASE_URL", DefaultFallbackBaseUrl).TrimEnd('/');

        try
        {
            var installScript = ResolveInstallerScript(baseUrl, fallbackBaseUrl, out var activeBaseUrl);
            RunPowerShellInstaller(installScript, activeBaseUrl, fallbackBaseUrl);
            Console.WriteLine();
            Console.WriteLine("完成。请重新打开 Hermes。");
            Pause();
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine();
            Console.WriteLine("安装失败。请把这个窗口截图发给小马。");
            Console.WriteLine(ex.Message);
            Pause();
            return 1;
        }
    }

    private static string GetEnv(string name, string fallback)
    {
        var value = Environment.GetEnvironmentVariable(name);
        return string.IsNullOrWhiteSpace(value) ? fallback : value;
    }

    private static string ResolveInstallerScript(string baseUrl, string fallbackBaseUrl, out string activeBaseUrl)
    {
        var localScript = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "install.ps1");
        if (File.Exists(localScript))
        {
            activeBaseUrl = baseUrl;
            return localScript;
        }

        var tempScript = Path.Combine(Path.GetTempPath(), "xiaoma-hermes-install.ps1");
        try
        {
            DownloadInstallerScript(baseUrl + "/install.ps1", tempScript);
            activeBaseUrl = baseUrl;
            return tempScript;
        }
        catch (Exception firstError)
        {
            Console.WriteLine("网站下载受限，改用备用入口。");
            Console.WriteLine(firstError.Message);
            DownloadInstallerScript(fallbackBaseUrl + "/install.ps1", tempScript);
            activeBaseUrl = fallbackBaseUrl;
            return tempScript;
        }
    }

    private static void DownloadInstallerScript(string url, string outputPath)
    {
        ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
        using (var client = new WebClient())
        {
            client.Headers.Add("User-Agent", "HermesZhCNSetup/2026.06.06");
            var script = client.DownloadString(url);
            if (!LooksLikeInstaller(script))
            {
                throw new InvalidDataException("下载内容不是安装器脚本：" + url);
            }
            File.WriteAllText(outputPath, script, new UTF8Encoding(true));
        }
    }

    private static bool LooksLikeInstaller(string script)
    {
        return script.IndexOf("param(", StringComparison.OrdinalIgnoreCase) >= 0
            && script.IndexOf("Hermes 中文增强", StringComparison.Ordinal) >= 0
            && script.IndexOf("Find-HermesCommand", StringComparison.Ordinal) >= 0;
    }

    private static void RunPowerShellInstaller(string scriptPath, string baseUrl, string fallbackBaseUrl)
    {
        var escapedScript = Quote(scriptPath);
        var escapedBase = Quote(baseUrl);
        var escapedFallback = Quote(fallbackBaseUrl);
        var info = new ProcessStartInfo
        {
            FileName = "powershell.exe",
            Arguments = "-NoProfile -ExecutionPolicy Bypass -File " + escapedScript
                + " -BaseUrl " + escapedBase
                + " -FallbackBaseUrl " + escapedFallback,
            UseShellExecute = false
        };

        using (var process = Process.Start(info))
        {
            if (process == null)
            {
                throw new InvalidOperationException("无法启动 PowerShell。");
            }
            process.WaitForExit();
            if (process.ExitCode != 0)
            {
                throw new InvalidOperationException("安装器退出码：" + process.ExitCode);
            }
        }
    }

    private static string Quote(string value)
    {
        return "\"" + value.Replace("\"", "\\\"") + "\"";
    }

    private static void Pause()
    {
        Console.WriteLine();
        Console.Write("按回车关闭窗口");
        Console.ReadLine();
    }
}
