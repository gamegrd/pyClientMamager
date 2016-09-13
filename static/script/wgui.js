var logStr = "";

function log(str) {
    logStr = str + "\n" + logStr;
    //最多存256k数据,太多了会卡
    if (logStr.length > 256 * 1024)
        logStr = ""
    $("#logtxt").textbox('setValue', logStr);
}


//修改游戏路径
function onChangeGamePath() {
    var path = $("#txt_gamePath").val()
    var checkNum = /^[A-Za-z]:.+.exe$/;
    if (!checkNum.test(path)) {
        $.messager.alert("", "路径不正确哟", "error");
        return;
    }

    SendMSG({
        "cmd": "changeGamePath",
        "path": path
    })
}


//修改登陆间隔时间(秒)
function onChangeLoginTimeComplete(val) {
    SendMSG({
        "cmd": "loginIntervalTime",
        "val": val
    })
}

function getDefaultSetting() {
    SendMSG({
        "cmd": "getDefaultSetting"
    }, function(data) {
        $("#txt_gamePath").textbox("setValue", data["path"]);
        $("#slider_IntervalTime").slider("setValue", data["intervalTime"]);
    });
}



function getCheckeduid() {
    var checkedItems = $('#dg_account').datagrid('getChecked');
    var names = [];
    $.each(checkedItems, function(index, item) {
        names.push(item.uid);
    });
    return names;
    //return $.toJSON(names)
}

function SendMSG(msg, callBack) {
    var data = $.toJSON(msg)
    $.ajax({
        type: 'post',
        traditional: true,
        contentType: "application/x-www-form-urlencoded; charset=UTF-8",
        url: '/sdk',
        data: {
            "pData": data
        },
        success: function(data) {
            //如果头里面已经标识了为 json 会自动解析
            //var rets = $.evalJSON(data);
            var rets = data;
            log(rets["msg"]);
            if (callBack)
                callBack(rets)
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            log("服务器异常: " + textStatus + "   " + data);

        },
    });

}

function accountContorl(cmd, val) {
    var accounts = getCheckeduid();
    if (0 == accounts.length) {
        log("想要登陆,你需要选择要操作的帐号");
        return;
    }

    var data = $.toJSON({
        "cmd": cmd,
        "val": val,
        "IDList": accounts
    })
    console.log(data)
    $.ajax({
        type: 'post',
        traditional: true,
        contentType: "application/x-www-form-urlencoded; charset=UTF-8",
        url: '/sdk',
        data: {
            "pData": data
        },
        success: function(data) {
            //var rets = $.evalJSON(data);
            var rets = data;
            log(rets["msg"]);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
            log("服务器异常: " + textStatus);

        },
    });

}



function pagerFilter(data) {
    if (typeof data.length == 'number' && typeof data.splice == 'function') { // is array
        data = {
            total: data.length,
            rows: data
        }
    }
    var dg = $(this);
    var opts = dg.datagrid('options');
    var pager = dg.datagrid('getPager');
    pager.pagination({
        onSelectPage: function(pageNum, pageSize) {
            opts.pageNumber = pageNum;
            opts.pageSize = pageSize;
            pager.pagination('refresh', {
                pageNumber: pageNum,
                pageSize: pageSize
            });
            console.log("dg.datagrid", data);
            dg.datagrid('loadData', data);
        }
    });

    if (!data.originalRows) {
        data.originalRows = (data.rows);
    }
    var start = (opts.pageNumber - 1) * parseInt(opts.pageSize);
    var end = start + parseInt(opts.pageSize);
    data.rows = (data.originalRows.slice(start, end));
    return data;
}


function refresh_dg_account(data) {
    var dg = $('#dg_account');
    var opts = dg.datagrid('options');
    var pager = dg.datagrid('getPager');
    //var data=getData(opts.pageNumber,opts.pageSize);
    var rows = dg.datagrid("getRows");
    var wgs = data["wgs"];
    var total = data["total"];
    var offset = rows.length - wgs.length;
    //数量变化时动态加减
    for (var i = 0; i < Math.abs(offset); i++) {
        if (offset < 0) {
            var k = rows.length;
            dg.datagrid('appendRow', {
                uid: wgs[k].uid,
                pid: wgs[k].pid,
                name: wgs[k].name,
                lv: wgs[k].lv,
                money: wgs[k].money,
            });
        } else {
            dg.datagrid('deleteRow', rows.length - 1);
        }
    }

    //加载所有
    for (var i = wgs.length - 1; i >= 0; i--) {
        //appendRow
        dg.datagrid('updateRow', {
            index: i,
            row: {
                uid: wgs[i].uid,
                pid: wgs[i].pid,
                name: wgs[i].name,
                lv: wgs[i].lv,
                money: wgs[i].money,
                note: wgs[i].note,
            }
        });
    };
    pager.pagination('refresh', { // change options and refresh pager bar information
        total: total
    });
    //setTimeout('refresh_dg_account()',3000); 
}

function ajaxloadData(start, num) {
    //console.log("start,num",(start-1)*num,num);
    var data = $.toJSON({
        "cmd": "getState",
        "start": (start - 1) * num,
        "num": num
    })
    try {
        $.ajax({
            type: 'post',
            traditional: true,
            url: '/sdk',
            data: {
                "pData": data
            },
            success: function(data) {
                //var rets = $.evalJSON(data);
                var rets = data;
                var dg = $('#dg_account');
                var opts = dg.datagrid('options');
                var pager = dg.datagrid('getPager');

                if (-1 == start) {
                    $('#dg_account').datagrid({
                        loadFilter: pagerFilter
                    }).datagrid('loadData', rets);
                } else {
                    if ((opts.pageNumber != start) || (num != opts.pageSize)) {
                        console.log("过期数据,不刷新");
                    } else {
                        refresh_dg_account(rets);
                    }

                }
                setTimeout('ajaxloadData(' + opts.pageNumber + ',' + opts.pageSize + ')', 1000);
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                log("服务器异常: " + textStatus);
                var dg = $('#dg_account');
                var opts = dg.datagrid('options');
                var pager = dg.datagrid('getPager');
                setTimeout('ajaxloadData(' + opts.pageNumber + ',' + opts.pageSize + ')', 2000);
            },
        });
    } catch (e) {}
}



//上传新帐号
function uploadAccounts () {
    var datastr=$("#textbox_uids").textbox('getValue')
    var str=datastr.split("\n"); 
    var accounts=[]
    var num=0;
    for (var i=0;i<str.length ;i++ )   
    {   
        var account=str[i].split(",");
        if (2==account.length)
        {
            accounts.push({"uid":account[0],"pwd":account[1]});
            num+=1;
        }
    }   
    log("共有合法帐号 " + num + " 组")
    SendMSG({"cmd":"uploadAccounts","accounts":accounts },function(data){
        $.messager.alert("", data["msg"], "info");
    });
}



//OnLoad

$(function() {
    getDefaultSetting();
    setTimeout('ajaxloadData(1,0)', 200);

});

try {
    if (window.console && window.console.log) {
        console.log("-----------------------------------------------------------\n");
        console.log("%c小帅哥，你想干嘛。。。\n", "color:green");
        console.log("%c不要乱来哦 有问题请联系:gamegrd@outlook.com", "color:green");
        console.log("-----------------------------------------------------------\n");
    }
} catch (e) {}