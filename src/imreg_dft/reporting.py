# -*- coding: utf-8 -*-

# reporting.py

# Copyright (c) 2014-?, Matěj Týč
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holders nor the names of any
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import contextlib

import numpy as np
# We intentionally don't import matplotlib on this level - we want this module
# to be importable even if one doesn't have matplotlib


@contextlib.contextmanager
def report_wrapper(orig, index):
    if orig is None:
        yield None
    else:
        prefix = "%03d-" % index
        orig.push_prefix(prefix)
        yield orig
        orig.pop_prefix(prefix)


class ReportsWrapper(object):
    """
    A wrapped dictionary.
    It allows a parent function to put it in a mode, in which it will
    prefix keys of items set.
    """
    def __init__(self, toshow=""):
        self.prefixes = [""]
        #: Keys by prefix
        self._stuff = {"": dict()}
        self.idx = ""
        self._toshow = toshow
        self._show = dict(
            inputs="i" in toshow,
            spectra="s" in toshow,
            logpolar="l" in toshow,
            tile_info="t" in toshow,
            scale_angle="1" in toshow,
            transformed="a" in toshow,
            translation="2" in toshow,
        )

    def get_contents(self):
        ret = self._stuff.items()
        return ret

    def copy_empty(self):
        ret = ReportsWrapper(self._toshow)
        ret.idx = self.idx
        ret.prefixes = self.prefixes
        for prefix in self.prefixes:
            ret._stuff[prefix] = dict()
        return ret

    def set_global(self, key, value):
        self._stuff[""][key] = value

    def get_global(self, key):
        ret = self._stuff[""][key]
        return ret

    def show(self, * args):
        ret = False
        for arg in args:
            ret |= self._show[arg]
        return ret

    def __setitem__(self, key, value):
        self._stuff[self.idx][key] = value

    def __getitem__(self, key):
        ret = self._stuff[self.idx][key]
        return ret

    def push_prefix(self, idx):
        self._stuff.setdefault(idx, dict())
        self.idx = idx
        self.prefixes.append(self.idx)

    def pop_prefix(self, idx):
        assert self.prefixes[-1] == idx, \
            ("Real previous prefix ({}) differs from the specified ({})"
             .format(self.prefixes[-1], idx))
        assert len(self.prefixes) > 1, \
            "There is not more than 1 prefix left, you can't remove any."
        self.prefixes.pop()
        self.idx = self.prefixes[-1]


class Rect_callback(object):
    def __call__(self, idx, LLC, dims):
        self._call(idx, LLC, dims)

    def _call(idx, LLC, dims):
        raise NotImplementedError()


class Rect_mpl(Rect_callback):
    """
    A class that can draw image tiles nicely
    """
    def __init__(self, subplot, shape):
        self.subplot = subplot
        self.ecs = ("w", "k")
        self.shape = shape

    def _get_color(self, coords, dic=None):
        lidx = sum(coords)
        ret = self.ecs[lidx % 2]
        if dic is not None:
            dic["ec"] = ret
        return ret

    def _call(self, idx, LLC, dims, special=False):
        import matplotlib.pyplot as plt
        # Get from the numpy -> MPL coord system
        LLC = LLC[::-1]
        URC = LLC + np.array((dims[1], dims[0]))
        kwargs = dict(fc='none', lw=4, alpha=0.5)
        coords = np.unravel_index(idx, self.shape)
        color = self._get_color(coords, kwargs)
        if special:
            kwargs["fc"] = 'w'
        rect = plt.Rectangle(LLC, dims[1], dims[0], ** kwargs)
        self.subplot.add_artist(rect)
        center = (URC + LLC) / 2.0
        self.subplot.text(center[0], center[1],
                          "%02d\n(%d, %d)" % (idx, coords[0], coords[1]),
                          va="center", ha="center", color=color)


def slices2rects(slices, rect_cb):
    """
    Args:
        slices: List of slice objects
        rect_cb (callable): Check :class:`Rect_callback`.
    """
    for ii, (sly, slx) in enumerate(slices):
        LLC = np.array((sly.start, slx.start))
        URC = np.array((sly.stop,  slx.stop))
        dims = URC - LLC
        rect_cb(ii, LLC, dims)


def imshow_spectra(fig, spectra):
    import matplotlib.pyplot as plt
    import mpl_toolkits.axes_grid1 as axg
    dfts_filt_extent = (-0.5, 0.5, -0.5, 0.5)
    grid = axg.ImageGrid(
        fig, 111, nrows_ncols=(1, 2),
        add_all=True,
        axes_pad=0.4, label_mode="L",
        cbar_pad=0.05, cbar_mode="each", cbar_size="3.5%",
    )
    what = ("template", "subject")
    for ii, im in enumerate(spectra):
        grid[ii].set_title("log abs dfts - %s" % what[ii])
        im = grid[ii].imshow(np.log(np.abs(im)), cmap=plt.cm.viridis,
                             extent=dfts_filt_extent, )
        grid[ii].set_xlabel("X / px")
        grid[ii].set_ylabel("Y / px")
        grid.cbar_axes[ii].colorbar(im)
    return fig


def imshow_logpolars(fig, spectra):
    import matplotlib.pyplot as plt
    import mpl_toolkits.axes_grid1 as axg
    logpolars_extent = (0, 0.5, 0, 180)
    grid = axg.ImageGrid(
        fig, 111, nrows_ncols=(2, 1),
        add_all=True,
        aspect=False,
        axes_pad=0.4, label_mode="L",
        cbar_pad=0.05, cbar_mode="each", cbar_size="3.5%",
    )
    ims = [np.log(np.abs(im)) for im in spectra]
    vmin = min([np.percentile(im, 2) for im in ims])
    vmax = max([np.percentile(im, 98) for im in ims])
    for ii, im in enumerate(ims):
        im = grid[ii].imshow(im, cmap=plt.cm.viridis, vmin=vmin, vmax=vmax,
                             aspect="auto", extent=logpolars_extent)
        grid[ii].set_xlabel("log radius")
        grid[ii].set_ylabel("azimuth / degrees")
        grid.cbar_axes[ii].colorbar(im)

    return fig


def imshow_plain(fig, images, what, also_common=False):
    import matplotlib.pyplot as plt
    import mpl_toolkits.axes_grid1 as axg
    ncols = len(images)
    nrows = 1
    if also_common:
        nrows = 2
    grid = axg.ImageGrid(
        fig, 111,  nrows_ncols=(nrows, ncols), add_all=True,
        axes_pad=0.4, label_mode="L",
        cbar_pad=0.05, cbar_mode="each", cbar_size="3.5%",
    )
    images = [im.real for im in images]

    for ii, im in enumerate(images):
        vmin = np.percentile(im, 2)
        vmax = np.percentile(im, 98)
        grid[ii].set_title("individual cmap --- {}".format(what[ii]))
        img = grid[ii].imshow(im, cmap=plt.cm.gray,
                              vmin=vmin, vmax=vmax)
        grid.cbar_axes[ii].colorbar(img)

    if also_common:
        vmin = min([np.percentile(im, 2) for im in images])
        vmax = max([np.percentile(im, 98) for im in images])
        for ii, im in enumerate(images):
            grid[ii + ncols].set_title("common cmap --- {}".format(what[ii]))
            im = grid[ii + ncols].imshow(im, cmap=plt.cm.viridis,
                                         vmin=vmin, vmax=vmax)
            grid.cbar_axes[ii + ncols].colorbar(im)

    return fig


def imshow_pcorr(fig, raw, filtered, extent, result, success, log_base=None):
    import matplotlib.pyplot as plt
    import mpl_toolkits.axes_grid1 as axg
    grid = axg.ImageGrid(
        fig, 111,  # similar to subplot(111)
        nrows_ncols=(1, 2),
        add_all=True,
        axes_pad=0.4,
        aspect=False,
        cbar_pad=0.05,
        label_mode="L",
        cbar_mode="single",
        cbar_size="3.5%",
    )
    vmax = raw.max()
    imshow_kwargs = dict(
        vmin=0, vmax=vmax,
        aspect="auto",
        origin="lower", extent=extent,
        cmap=plt.cm.viridis,
    )
    grid[0].set_title("pcorr --- original")
    labels = ("translation y / px", "translation x / px")
    grid[0].imshow(raw, ** imshow_kwargs)

    center = np.array(result)
    # Otherwise plot would change xlim
    grid[0].autoscale(False)
    grid[0].plot(center[0], center[1], "o",
                 color="r", fillstyle="none", markersize=18, lw=8)
    grid[0].annotate("succ: {:.3g}".format(success), xy=center,
                     xytext=(0, 8), textcoords='offset points',
                     color="red", va="bottom", ha="center")
    grid[1].set_title("pcorr --- constrained and filtered")
    im = grid[1].imshow(filtered, ** imshow_kwargs)
    grid.cbar_axes[0].colorbar(im)

    if log_base is not None:
        for dim in range(2):
            grid[dim].set_xscale("log", basex=log_base)
            grid[dim].get_xaxis().set_major_formatter(plt.ScalarFormatter())
            xlabels = grid[dim].get_xticklabels(False, "both")
            for x in xlabels:
                x.set_ha("right")
                x.set_rotation_mode("anchor")
                x.set_rotation(40)
        labels = ("rotation / degrees", "scale change")

    # The common stuff
    for idx in range(2):
        grid[idx].grid(c="w")
        grid[idx].set_xlabel(labels[1])

    grid[0].set_ylabel(labels[0])

    return fig


def imshow_tiles(fig, im0, slices, shape):
    import matplotlib.pyplot as plt
    axes = fig.add_subplot(111)
    axes.imshow(im0, cmap=plt.cm.viridis)
    callback = Rect_mpl(axes, shape)
    slices2rects(slices, callback)


def imshow_results(fig, successes, shape):
    import matplotlib.pyplot as plt
    toshow = successes.reshape(shape)

    axes = fig.add_subplot(111)
    img = axes.imshow(toshow, cmap=plt.cm.viridis, interpolation="none")
    fig.colorbar(img)

    axes.set_xticks(np.arange(shape[1]))
    axes.set_yticks(np.arange(shape[0]))

    coords = np.unravel_index(np.arange(len(successes)), shape)
    for idx, coord in enumerate(zip(* coords)):
        label = "{:02d}\n({},{})".format(idx, coord[1], coord[0])
        axes.text(coord[1], coord[0], label,
                  va="center", ha="center", color="r",)


def mk_factory(prefix, basedim, dpi=150, ftype="png"):
    import matplotlib.pyplot as plt

    @contextlib.contextmanager
    def _figfun(basename, x, y, use_aspect=True):
        _basedim = basedim
        if use_aspect is False:
            _basedim = basedim[0]
        fig = plt.figure(figsize=_basedim * np.array((x, y)))
        yield fig
        fname = "{}{}.{}".format(prefix, basename, ftype)
        fig.savefig(fname, dpi=dpi, bbox_inches="tight")
        del fig

    return _figfun


def report_tile(reports, prefix, multiplier=5.5):
    multiplier = reports.get_global("size")
    dpi = reports.get_global("dpi")
    ftype = reports.get_global("ftype")

    aspect = reports.get_global("aspect")
    basedim = multiplier * np.array((aspect, 1), float)
    for index, contents in reports.get_contents():
        fig_factory = mk_factory("{}-{}".format(prefix, index),
                                 basedim, dpi, ftype)
        for key, value in contents.items():
            if "ims-filt" in key and reports.show("inputs"):
                with fig_factory(key, 2, 2) as fig:
                    imshow_plain(fig, value, ("template", "subject"), True)
            elif "dfts-filt" in key and reports.show("spectra"):
                with fig_factory(key, 2, 1, False) as fig:
                    imshow_spectra(fig, value)
            elif "logpolars" in key and reports.show("logpolar"):
                with fig_factory(key, 1, 1.4, False) as fig:
                    imshow_logpolars(fig, value)
            elif "amas-orig" in key and reports.show("scale_angle"):
                with fig_factory("sa", 2, 1) as fig:
                    center = np.array(contents["amas-result"], float)
                    center[0] = 1.0 / center[0]
                    imshow_pcorr(
                        fig, value, contents["amas-postproc"],
                        contents["amas-extent"], center,
                        contents["amas-success"], log_base=contents["base"]
                    )
            elif "tiles-successes" in key and reports.show("tile_info"):
                with fig_factory("tile-successes", 1, 1) as fig:
                    imshow_results(fig, value, reports.get_global("tiles-shape"))
            elif "tiles-decomp" in key and reports.show("tile_info"):
                with fig_factory("tile-decomposition", 1, 1) as fig:
                    imshow_tiles(fig, reports.get_global("tiles-whole"),
                                 value, reports.get_global("tiles-shape"))
            elif "after-rot" in key and reports.show("transformed"):
                # TODO: Show: Original, rotated, translated0, translated180.
                with fig_factory(key, 3, 1) as fig:
                    imshow_plain(fig, value,
                                 ("template", "subject", "tformed subject"))
            elif "t0-orig" in key and reports.show("translation"):
                t_flip = ("0", "180")
                for idx in range(2):
                    basename = "t_{}".format(t_flip[idx])
                    with fig_factory(basename, 2, 1) as fig:
                        img = contents["t{}-orig".format(idx)]
                        halves = np.array(img.shape) / 2.0
                        extent = np.array((- halves[1], halves[1],
                                           - halves[0], halves[0]))
                        center = contents["t{}-tvec".format(idx)][::-1]
                        imshow_pcorr(
                            fig, img, contents["t{}-postproc".format(idx)],
                            extent, center, contents["t{}-success".format(idx)]
                        )
