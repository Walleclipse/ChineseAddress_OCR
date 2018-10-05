// pages/welcome/welcome.js
Page({

  data:{
    sliderList: [
      { selected: true, imageSource: '../../images/logo_v4.jpg' },
      { selected: false, imageSource: '../../images/deecamp.png' },
      { selected: false, imageSource: '../../images/cxgc.png' },
    ]
  },


  clickLogo: function () {
    wx.navigateTo({
      url: '../index/index'
    });
  },


  //轮播图绑定change事件，修改图标的属性是否被选中
  switchTab: function (e) {
    var sliderList = this.data.sliderList;
    var i, item;
    for (i = 0; item = sliderList[i]; ++i) {
      item.selected = e.detail.current == i;
    }
    this.setData({
      sliderList: sliderList
    });
  },

})