# Advanced WPF GUI Patterns in PowerShell

Use this guide when constructing multi-threaded Windows Presentation Foundation (WPF) applications or complex XAML layouts inside PowerShell.

## 1. Preventing UI Thread Locking (Runspaces)

By default, launching a GUI modal (`$Window.ShowDialog()`) blocks the PowerShell console. If a button click triggers a long-running system script, the UI will freeze and show "Not Responding" to the user.

To prevent this, run the background logic inside a separate **Runspace** and use the **Dispatcher** to update the UI thread.

```powershell
# Create shared thread-safe hash table
$SharedData = [hashtable]::Synchronized(@{})
$SharedData.Window = $Window
$SharedData.StatusText = $btnTxtStatus # Reference to status control

# Define background worker logic
$ScriptBlock = {
    param($Data)
    
    # Simulate heavy background Windows configuration task
    Start-Sleep -Seconds 5
    
    # Use Dispatcher to safely update the UI thread
    $Data.Window.Dispatcher.Invoke([action]{
        $Data.StatusText.Text = "Background configuration complete."
    })
}

# Setup background runspace pool
$RunspacePool = [runspacefactory]::CreateRunspacePool(1, 2)
$RunspacePool.Open()

# Execute background thread
$PowerShell = [powershell]::Create()
$PowerShell.RunspacePool = $RunspacePool
$PowerShell.AddScript($ScriptBlock).AddArgument($SharedData) | Out-Null
$PowerShell.BeginInvoke()
```

## 2. Dynamic XAML Layout Management

When designing adaptive corporate tools, avoid pinning strict visual coordinates (like `Canvas` with absolute `Left`/`Top` offsets). Instead, rely on auto-scaling grids, columns, and stack alignments.

### Casing and Namespace Pitfalls
- **Case Sensitivity:** Windows XAML parsers are strictly case-sensitive. `<button>` will crash compilation; always write `<Button>`.
- **Merged Resources:** Centralize theme variables locally inside shared resource dictionaries rather than repeating styling attributes across every button.
- **WPF Namespaces:** Always include the required namespace attributes in your root XAML tag:
  ```xml
  xmlns="http://schemas.microsoft.com/winfx/2000/xaml/presentation"
  xmlns:x="http://schemas.microsoft.com/winfx/2000/xaml"
  ```

## 3. Local Assembly Loading (Offline Boundaries)

In highly restrictive corporate environments, loading supplementary DLLs must be handled purely offline.

### Method 1: Loading GAC Assemblies (Global Assembly Cache)
Standard Windows GUI libraries exist in the GAC and can be loaded directly by short-name:
```powershell
Add-Type -AssemblyName PresentationFramework
```

### Method 2: Loading Local Side-loaded Assemblies
If utilizing specialized community extensions or SQLite local databases, side-load the raw DLL from a trusted, relative module folder path:
```powershell
[System.Reflection.Assembly]::LoadFrom("$PSScriptRoot\lib\System.Data.SQLite.dll")
```
> ⚠️ **Corporate Tip:** Check that any side-loaded binary compiles with a signed certificate matching your company's local Enterprise Trust Root CA to pass Windows AppLocker and Execution Policy constraints.
