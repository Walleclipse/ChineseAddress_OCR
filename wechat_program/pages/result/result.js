//index.js  
//获取应用实例  
var app = getApp()

// 引用地图微信小程序JSAPI模块 
var QQMapWX = require("../../libs/qqmap-wx-jssdk.js")
var demo = new QQMapWX({
  key: 'SZ6BZ-TFGKW-NC3R5-RIPUE-XYXNS-JWBJZ' // 必填
});

App({
  onLaunch: function () { }
})


Page({

  /**
   * 页面的初始数据
   */

  data: {
    // 地址识别用
    // tempFilePaths: '../../images/logo.png',
    tempFilePaths_bbox: '../../images/logo.png',
    addrline: 'aaaaa',

    // 腾讯地图定位用
    key: 'SZ6BZ-TFGKW-NC3R5-RIPUE-XYXNS-JWBJZ',
    latitude: '',
    longitude: '',
    resturant: [],
    markers: [],
    poi_flag: false,

  },

  clickLogo: function () {
    wx.navigateTo({
      url: '../result/result'
    });
  },

  onLoad: function (options) {
    // 生命周期函数--监听页面加载
    console.log(options)
    this.setData({
      tempFilePaths_bbox: options.a,
      addrline: options.b
    })
  },

  // 选择图片并上传
  upLoad: function () {
    var _this = this
    wx.chooseImage({
      count: 1,
      sizeType: ['original'],
      sourceType: ['album', 'camera'], // 来源是相册、相机
      success: function (res) {
        var tempFilePaths = res.tempFilePaths
        _this.setData({
          tempFilePaths: res.tempFilePaths,
          showView: false
        })
        wx.showLoading({
          title: '图片上传中。。。'
        })

        wx.uploadFile({
          url: 'https://www.lihao7086.com/upload', //上传接口地址
          filePath: tempFilePaths[0],
          name: 'file',
          formData: {
            'user': 'test'
          },
          success: function (res) {
            console.log('uploadFileSuccess')
            var data = res.data //get image file name
            _this.setData({
              content: '上传中。。。'
            })
            wx.downloadFile({
              url: 'https://www.lihao7086.com/download_img/' + data,
              success: function (res) {
                wx.hideLoading()
                wx.showToast({
                  title: '识别成功',
                  icon: 'success',
                  mask: true,
                  duration: 1000
                })

                _this.setData({
                  tempFilePaths_bbox: res.tempFilePath,
                  content: '上传成功',
                  showView: (!_this.data.showView)
                })

                wx.request({
                  url: 'https://www.lihao7086.com/download_txt',
                  success: function (res) {
                    _this.setData({
                      addrline: res.data
                    })
                  }
                })
              }
            })
          },
          fail: function (res) {
            wx.hideLoading()
            wx.showModal({
              title: '提示',
              content: '上传失败，请检查网络连接',
              showCancel: false
            })
            console.log('uploadFile fail')
            console.log(res)
            _this.setData({
              content: '上传失败，请检查网络连接'
            })
          }
        })

        wx.navigateTo({
          url: '../result/result'
        });
      },
    })
  },

  // 返回
  click_return: function () {
    this.setData({
      latitude: '',
      longitude: '',
      resturant: [],
      markers: [],
    })
    wx.reLaunch({
      url: '../index/index'
    })
  },

  // 地址定位 
  seeMap: function () {
    var _this = this;
    demo.geocoder({
      address: _this.data.addrline,
      success: function (res) {
        var address_component = res.result.address_components;
        var results = address_component.province + address_component.city + address_component.district + address_component.street + address_component.street_number;
        _this.setData({
          latitude: res.result.location.lat,
          longitude: res.result.location.lng,
          markers: [{
            id: '00000',
            latitude: res.result.location.lat,
            longitude: res.result.location.lng,
            iconPath: '../../images/marker_red.png',
            width: 23,
            height: 30,
          }],
          address_component: results,
        })
        console.log(_this.data.latitude)
        console.log(_this.data.longitude)

        _this.request_poi();
        setTimeout(function () {
          var _resturant = _this.data.resturant
          var markers_new = _this.data.markers
          for (var i = 0; i < _resturant.length; ++i) {
            markers_new.push({
              id: _resturant[i].id,
              latitude: _resturant[i].location.lat,
              longitude: _resturant[i].location.lng,
              iconPath: '../../images/marker_blue.png',
              width: 23,
              height: 30,
            })
          }
          console.log(_resturant)
          _this.setData({
            markers: markers_new,
          })
          console.log(_this.data.markers)
        }, 500)
      },

      fail: function (res) {
        wx.showModal({
          title: '提示',
          content: '查询无结果',
          showCancel: false,
        })
        console.log(res);
      },
      complete: function (res) {
        console.log(res);
      }
    });
  },

  //点击地图标记点时触发，显示周边信息，改变标记点颜色
  makertap: function (e) {
    var _this = this;
    var id = e.markerId;
    _this.showSearchInfo(_this.data.resturant, id);
    _this.changeMarkerColor(_this.data.resturant, _this.data.markers, id);
  },

  //上面方法调用，获得周边信息setData渲染到页面里
  showSearchInfo: function (data, id) {
    var _this = this;
    for (var i = 0; i < data.length; i++) {
      if (data[i].id == id) {
        var title = data[i].title;
        var address = data[i].address;
      }
    }
    _this.setData({
      placeData: {
        title: '名称：' + title + '\n',
        address: '地址：' + address + '\n',
        // telephone: data[i].telephone == undefined ? '电话：暂无信息' : '电话：' + data[i].telephone
      }
    });
    if (data[i].id == '00000') {
      _this.setData({
        placeData: {
          title: '定位点',
          address: '',
        }
      });
    }
  },

  //上面方法调用，改变标记点颜色
  changeMarkerColor: function (data, markers, id) {
    if (id != '0000') {
      var _this = this;
      var markersTemp = [];
      markersTemp[0] = markers[0]
      for (var i = 0; i < data.length; i++) {
        if (data[i].id == id) {
          markers[i + 1].iconPath = "../../images/marker_red.png";
        } else {
          markers[i + 1].iconPath = "../../images/marker_blue.png";
          markers[0].iconPath = "../../images/marker_red.png";
        }
        markersTemp[i + 1] = markers[i + 1];
      }
      console.log(markersTemp)
      _this.setData({
        markers: markersTemp
      });
    }
  },

  //请求POI的数据
  request_poi: function () {
    var _this = this
    // 发起POI检索请求 
    demo.search({
      keyword: '餐饮',
      location: {
        latitude: _this.data.latitude,
        longitude: _this.data.longitude,
      },
      success: function (res) {
        console.log(_this.data.latitude)
        console.log(res.data)
        var _that = _this
        _that.setData({
          resturant: res.data,
          poi_flag: true,
        })
        console.log(_that.data.poi_flag)
      }
    });
  },
})