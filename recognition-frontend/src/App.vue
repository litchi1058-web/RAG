<template>
  <div id="app"><router-view /></div>
</template>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { height:100%; font-family:"Microsoft YaHei",-apple-system,sans-serif; background:#F0F2F5; }
#app { height:100%; min-height:100vh; }
.el-card { border:1px solid #E8E8E8 !important; box-shadow:0 1px 4px rgba(0,0,0,0.06) !important; border-radius:8px !important; }
.el-table { border:1px solid #E8E8E8; border-radius:8px; }
.el-table th { background:#FAFAFA !important; font-weight:600; color:#1A1A2E; }
</style>
